
import MyUtils

config = { 'DB_HOST':'127.0.0.1','DB_USER':'wordgame2dev','DB_PASSWD':'wordgame2','DB':'wordGameDB'}


words = []
for line in open("allWords.txt"):
    currentWord = line.strip().lower()
    words.append(currentWord)



with MyUtils.UseDatabase(config) as cursor:
    SQL = """insert into allWords (word) values (%s)"""
    for e in words:
        cursor.execute(SQL, (e.title(),))


