def test(a:list[str]=["a", "b", "c"]) -> list[str]:
    print(a)
    return a


if __name__ == "__main__":
    a = test()
    print(a)
    a.pop()
    print(a)
    a = test()
    print(a)