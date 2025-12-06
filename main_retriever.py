from DATABASE.config import cruder
from data_retriever import FileRetriever
import asyncio
import pandas as pd
from CUSTOMIZED.cust_logger import logger
from CUSTOMIZED.cust_retrier import Retrier

class ICTRetrieveRunner:

    DICT_FR : dict[str, FileRetriever] = {} #메모이제이션 용

    def __init__(self):
        pass

    async def run(self):

        df_instrument : pd.DataFrame = pd.DataFrame(await cruder.get_instrument_infos())
        tasks : list[asyncio.Task] = []
        
        for row in df_instrument.itertuples(index=False):
            instrument_name:str = row.name
            host:str = row.host 
            user:str = row.user
            port:int = row.port
            dir_base_source:str = row.dir_base_source
            dir_base_destination:str = row.dir_base_destination
            ssh_key_path:str = row.ssh_key_path 

            if instrument_name not in self.DICT_FR:
                fr = FileRetriever(cruder).set_instrument_infos(instrument_name, host, user, port, ssh_key_path, dir_base_source, dir_base_destination)
                await fr.connect_to_instrument()
                self.DICT_FR[instrument_name] = fr
            else:
                fr = self.DICT_FR[instrument_name]

            retrier = Retrier.retry(lambda: fr.run(50), on_retry=lambda: fr.connect_to_instrument())
            tasks.append(asyncio.create_task(retrier))

            # 문제시 이걸로 백업
            # fr = FileRetriever(cruder).set_instrument_infos(instrument_name, host, user, port, ssh_key_path, dir_base_source, dir_base_destination)
            # await fr.connect_to_instrument()
            # tasks.append(asyncio.create_task(fr.run(50)))


        await asyncio.gather(*tasks, return_exceptions=True)

if __name__ == "__main__":
    asyncio.run(ICTRetrieveRunner().run())



