def number_to_base(n: int, b: int) -> list[int]:
    if n == 0:
        return [0]
    digits = []
    while n:
        digits.append(int(n % b))
        n //= b
    return digits[::-1]


def to_base(n: int, base: list) -> str:
    if n == 0:
        return ""

    b = len(base)
    res = ""

    while n:
        res += base[int(n % b)]
        n //= b
    return res[::-1]


def from_base(expr: str, base: int) -> int:
    return sum(
        [int(character) * base**index for index, character in enumerate(expr[::-1])]
    )
