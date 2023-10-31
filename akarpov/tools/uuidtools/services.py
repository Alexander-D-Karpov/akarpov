import datetime
from uuid import UUID


def uuid1_time_to_datetime(time: int):
    return datetime.datetime(1582, 10, 15) + datetime.timedelta(microseconds=time // 10)


version_info = {
    1: """UUID Version 1 (Time-Based): The current time and the specific MAC address of the computer generating the
    UUID are used to construct IDs in UUID version 1. This means that even if they generate UUIDs simultaneously,
    separate machines are probably going to produce different ones. If your clock also knew your computer’s unique
    number, it would display a different number each time you glanced at it depending on the time and who you were.
    When generating a UUID that is specific to a certain computer and linked to the moment it was generated,
    this version is frequently utilised.""",
    2: """V2 UUIDs include the MAC address of the generator, lossy timestamp, and an account ID such as user ID or
    group ID on the local computer. Because of the information included in the UUID, there is limited space for
    randomness. The clock section of the UUID only advances every 429.47 seconds (~7 minutes). During any 7 minute
    period, there are only 64 available different UUIDs! """,
    3: """UUID Version 3 (Name-Based, Using MD5):The UUID version 3 uses MD5 hashing to create IDs.
    It uses the MD5 technique to combine the “namespace UUID” (a unique UUID) and the name you supply to get a unique
    identification. Imagine it as a secret recipe book where you add a secret ingredient (namespace UUID) to a standard
    ingredient (name), and when you combine them using a specific method (MD5), you get a unique dish (UUID).
    When you need to consistently produce UUIDs based on particular names, this variant is frequently utilised.""",
    4: """UUID Version 4 (Random): UUID version 4 uses random integers to create identifiers. It doesn’t depend on
    any particular details like names or times. Instead, it simply generates a slew of random numbers and characters.
    Imagine shaking a dice-filled box and then examining the face-up numbers that came out. It resembles receiving an
    unpredictable combination each time. When you just require a single unique identification without any kind of
    pattern or order, this version is fantastic.""",
    5: """UUID Version 5 (Name-Based, Using SHA-1): Similar to version 3, UUID version 5 generates identifiers using
    the SHA-1 algorithm rather than the MD5 technique. Similar to version 3, you provide it a “namespace UUID” and a
    name, and it uses the SHA-1 technique to combine them to get a unique identification. Consider it similar to
    baking a cake: you need a special pan (namespace UUID), your recipe (name), and a particular baking technique (
    SHA-1). No matter how many times you cook this recipe, you will always end up with a unique cake (UUID). Similar
    to version 3, UUID version 5 is frequently used in situations where a consistent and distinctive identity based
    on particular names is required. The better encryption capabilities of SHA-1 make its use preferred over MD5 in
    terms of security.""",
}


def decode_uuid(token: str) -> dict:
    data = {"token": token}
    try:
        uuid = UUID(token)
    except ValueError:
        return {"message": "not a valid UUID token"}
    data["version"] = f"{uuid.version}, {uuid.variant}"
    data["hex"] = uuid.hex
    data["bytes"] = bin(uuid.int)[2:]
    data["num"] = uuid.int
    if uuid.version == 1:
        data["time"] = uuid1_time_to_datetime(uuid.time)

    if uuid.version in version_info:
        data["info"] = version_info[uuid.version]
    return data
