from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.cron import CronTrigger
import asyncio
from data_retriever_defect import sync_external_defect_data
import CUSTOMIZED.cust_logger as logger

async def main():
    try:
        scheduler = AsyncIOScheduler()
        
        # 평일 08:00, 10:00, 12:00, 14:00, 16:00, 18:00, 20:00에 실행
        scheduler.add_job(sync_external_defect_data, args=["시장불량"], trigger = CronTrigger(minute='*'))
        scheduler.start()
        
        # 무한 루프 (조용히 대기)
        while True:
            await asyncio.sleep(3600)  # 1시간마다 체크
            
    except KeyboardInterrupt:
        logger.info("스케줄러 종료 중...")
        scheduler.shutdown()
        logger.info("스케줄러 종료됨")
    except Exception as e:
        logger.error(f"스케줄러 오류: {e}")
        scheduler.shutdown()

if __name__ == "__main__":
    asyncio.run(main())
