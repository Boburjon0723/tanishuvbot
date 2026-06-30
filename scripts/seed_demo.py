"""Demo foydalanuvchilarni bazaga qo'shish: 5 erkak + 5 ayol."""

import asyncio

from database.connections import Database
from database.queries import get_user

DEMO_MALES = [
    (900001, "Alisher", 24, "Toshkent", "Sport bilan shug'ullanaman, sayohat qilishni yaxshi ko'raman."),
    (900002, "Bobur", 22, "Samarqand", "Kitob o'qish va musiqa — mening hobbilarim."),
    (900003, "Dilshod", 26, "Buxoro", "Dasturchiman, yangi odamlar bilan tanishishni xohlayman."),
    (900004, "Jasur", 23, "Andijon", "Tabiat va foto suratga olish — sevimli mashg'ulotlarim."),
    (900005, "Kamol", 25, "Farg'ona", "Ochiq fikrli va pozitiv odamman."),
]

DEMO_FEMALES = [
    (900006, "Dilnoza", 21, "Toshkent", "San'at va dizayn bilan shug'ullanaman."),
    (900007, "Malika", 23, "Samarqand", "Yaxshi suhbat va samimiy munosabat qidiryapman."),
    (900008, "Nigora", 22, "Buxoro", "Sayohat va yangi taomlar tatib ko'rishni yaxshi ko'raman."),
    (900009, "Sevara", 24, "Andijon", "O'qish va rivojlanish — hayotimdagi ustuvor yo'nalish."),
    (900010, "Zarina", 20, "Namangan", "Kulgi va iliq muhit yaratishni bilaman."),
]

FALLBACK_PHOTO = "AgACAgIAAxkBAAIBY2Zdemo_placeholder_photo_id"


async def get_photo_id(db: Database) -> str:
    row = await db.fetchone(
        "SELECT photo_id FROM users WHERE photo_id IS NOT NULL AND photo_id != '' LIMIT 1"
    )
    if row and row.get("photo_id"):
        return row["photo_id"]
    return FALLBACK_PHOTO


async def upsert_demo(
    db: Database,
    telegram_id: int,
    name: str,
    age: int,
    gender: str,
    target_gender: str,
    city: str,
    bio: str,
    photo_id: str,
) -> None:
    existing = await get_user(db, telegram_id)
    if existing:
        await db.execute(
            """
            UPDATE users SET
                name = ?, age = ?, gender = ?, target_gender = ?,
                city = ?, photo_id = ?, bio = ?, is_active = 1
            WHERE telegram_id = ?
            """,
            name,
            age,
            gender,
            target_gender,
            city,
            photo_id,
            bio,
            telegram_id,
        )
        print(f"  Yangilandi: {name} ({gender})")
        return

    await db.execute(
        """
        INSERT INTO users (
            telegram_id, name, age, gender, target_gender, city, photo_id, bio, is_active
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, 1)
        """,
        telegram_id,
        name,
        age,
        gender,
        target_gender,
        city,
        photo_id,
        bio,
    )
    print(f"  Qo'shildi: {name} ({gender})")


async def main() -> None:
    db = Database()
    await db.connect()

    photo_id = await get_photo_id(db)
    if photo_id == FALLBACK_PHOTO:
        print("Diqqat: bazada rasm yo'q — avval o'zingiz ro'yxatdan o'ting, keyin qayta ishga tushiring.")
        print("Hozircha placeholder photo_id ishlatiladi (rasm chiqmasligi mumkin).\n")
    else:
        print("Mavjud foydalanuvchi rasmi demo profillar uchun ishlatiladi.\n")

    print("Erkaklar:")
    for tid, name, age, city, bio in DEMO_MALES:
        await upsert_demo(db, tid, name, age, "male", "female", city, bio, photo_id)

    print("\nAyollar:")
    for tid, name, age, city, bio in DEMO_FEMALES:
        await upsert_demo(db, tid, name, age, "female", "male", city, bio, photo_id)

    total = await db.fetchone("SELECT COUNT(*) AS cnt FROM users WHERE telegram_id >= 900001")
    print(f"\nTayyor! Demo profillar: {total['cnt'] if total else 0} ta")

    await db.close()


if __name__ == "__main__":
    asyncio.run(main())
