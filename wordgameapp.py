import random
import time
from flask import Flask, render_template, session, url_for, request, flash, redirect
import MyUtils

config = { 'DB_HOST':'127.0.0.1','DB_USER':'wordgame2dev','DB_PASSWD':'wordgame2','DB':'wordGameDB'}

app = Flask(__name__)

# HighScore object for use in sorting high scores list
class HighScore:
    def __init__(self, time, name):
        self.time = time
        self.name = name
 
@app.route('/')
def show_home_page():
    return render_template("HomePage.html",
                           page_title = "Welcome to the Word Game",
                           last_player = session.get("lastPlayer", "noNameDefault"),
                           last_score = session.get("timeTaken", "0"),
                           play_url = url_for("start_new_game"),
                           top_scores_url = url_for("view_high_scores"), )

@app.route('/playgame')
def start_new_game():
    session['storedHighScore'] = False

    with MyUtils.UseDatabase(config) as cursor:
        SQL = """select word from allWords where CHAR_LENGTH(word) > 6 ORDER BY RAND() LIMIT 1"""
        cursor.execute( SQL )
        the_data = cursor.fetchall()

    sourceWord= ""
    for row in the_data:
        sourceWord = row[0].title().strip()
    

    session['sourceWord'] = sourceWord
    session['startTime'] = time.time()
    
    return render_template("PlayGame.html",
                           page_title = "Play Game",
                           chosen_word = session.get("sourceWord"),
                           home_url = url_for("show_home_page"),
                           submit_url = url_for("show_game_result"), )

@app.route('/gameresult', methods = ["POST"])
def show_game_result():
    session['endTime'] = time.time()

    #with MyUtils.UseDatabase(config) as cursor:
    #    SQL = """select word from allWords"""
    #    cursor.execute( SQL )
    #    the_data = cursor.fetchall()




    #listOfLegalWords = []

    #for row in the_data:
    #    listOfLegalWords.append(row[0].strip().lower())

    sourceWord = session.get("sourceWord")
    listOfEntries = [request.form['word1'].strip(), request.form['word2'].strip(), request.form['word3'].strip(),
                     request.form['word4'].strip(), request.form['word5'].strip(), request.form['word6'].strip(),
                     request.form['word7'].strip()]

    legalPlayerWords = []
    illegalPlayerWords = []
    for wordEntry in listOfEntries:
        entryAsAList = list(wordEntry.lower())
        sourceWordAsAList = list(sourceWord.lower())
        wordEntryInLowerCase = wordEntry.lower()
        illegalWord = {}
        legalWord = True

        # Check that the entry is longer than 3 characters in length
        if entryAsAList.__len__() < 3:
            illegalWord['Reason'] = "The word is under 3 characters in length."
            legalWord = False

        # Check that the letters used are in the source word
        indexPosition = 0
        while legalWord == True and indexPosition < entryAsAList.__len__():
            characterAtIndex = entryAsAList[indexPosition]
            if characterAtIndex in sourceWordAsAList:
                sourceWordAsAList.remove(characterAtIndex)
                indexPosition = indexPosition + 1
            else:
                illegalWord['Reason'] = "The word contained letters which were not in the source word."
                legalWord = False

        # Check that the entry is a real word(access table here)
        if legalWord == True:
            with MyUtils.UseDatabase(config) as cursor:
                SQL = """select * from allWords where word = 'wordEntry'"""
                cursor.execute( SQL )
                the_data = cursor.fetchall()




            #listOfLegalWords = []

            for row in the_data:
                if len(row[0].strip().lower()) == 0:
                    illegalWord['Reason'] = "The word is not a real word."
                    legalWord = False

            #if wordEntryInLowerCase not in listOfLegalWords:
            #    illegalWord['Reason'] = "The word is not a real word."
            #    legalWord = False

        # Check that the word is not a duplicate
        if legalWord == True:
            if wordEntryInLowerCase in legalPlayerWords:
                illegalWord['Reason'] = "The word entered is a duplicate."
                legalWord = False

        # Check that the entry is not the source word
        if legalWord == True:
            if wordEntryInLowerCase == sourceWord.lower():
                illegalWord['Reason'] = "The word entered matched the source word."
                legalWord = False

        if legalWord == True:
            legalPlayerWords.append(wordEntryInLowerCase)
        else:
            illegalWord['Word'] = wordEntry
            illegalPlayerWords.append(illegalWord)

    # Process how long it took the player to complete the game
    finishTime = session.get("endTime")
    startingTime = session.get("startTime")
    session['timeTaken'] = ("%.3f" % float(finishTime - startingTime))

    failureRemarks = ["Failing at such an easy game. You must be so proud of yourself!",
                      "You had one job and you messed it up!.",
                      "I sincerely hope that this effort was meant as a joke.",
                      "You must be exhausted from all of that thinking. Then again, it dosen't look like you were doing much thinking there.",
                      "But you were going so well! That was sarcasm, just in case you didn't notice.",
                      "So much thought. So little end product."]

    # Process session variables for if the game was won or lost
    if illegalPlayerWords.__len__() > 0:
        session["lastPlayer"] = "lostGameDefault"
    
    return render_template("DisplayResult.html",
                           page_title = "Game Results",
                           source_word = sourceWord,
                           legalWords = legalPlayerWords,
                           illegalWords = illegalPlayerWords,
                           game_time = session.get("timeTaken"),
                           failure_remark = random.choice(failureRemarks),
                           home_url = url_for("show_home_page"),
                           play_url = url_for("start_new_game"),
                           submit_score_url = url_for("store_high_score"), )

# Add the latest high score to the list
def updateHighScoresFile(timeTaken, lastPlayer):
    scoreToInput = [(timeTaken, lastPlayer),]

    with MyUtils.UseDatabase(config) as cursor:
        SQL = """insert into highscores (time, name) values (%s, %s)"""
        for e in scoreToInput:
            cursor.execute(SQL, (e[0], e[1].title()))


# Sort the high scores based on completion time -> returns a sorted list of objects
def getSortedHighScoresList():
    sortedList = []

    with MyUtils.UseDatabase(config) as cursor:
        SQL = """select time,name from highscores Order by time"""
        cursor.execute( SQL )
        the_data = cursor.fetchall()


    for row in the_data:
        print(str(row[0])+" "+row[1].strip().lower())
        timeAchieved = row[0]
        nameEntered = row[1].strip().lower()
        sortedList.append(HighScore(timeAchieved,nameEntered))

    print(sortedList)
    return sortedList

@app.route('/newhighscore', methods = ["POST"])
def store_high_score():
    session['lastPlayer'] = request.form['userName']

    if session.get("storedHighScore") == False:
        # Place the new high score into the high scores file
        updateHighScoresFile(session.get("timeTaken"), session.get("lastPlayer"))
        session['storedHighScore'] = True
        
    # Get the sorted list of high scores & convert back to a list of strings
    listOfAllHighScores = getSortedHighScoresList()
    sortedListOfScores = []
    for scoreObject in listOfAllHighScores:
        sortedListOfScores.append(str(scoreObject.time) + " " + scoreObject.name)
        
    # Find where the players score ranks in the list
    if listOfAllHighScores.__len__() > 1:
        currentScore = session.get("timeTaken") + " " + session.get("lastPlayer")
        highScorePosition = sortedListOfScores.index(currentScore) + 1#occasional issue here
    else:
        highScorePosition = 1

    # Decide what superscript is needed after the ranking position
    superscript = ""
    if highScorePosition % 10 == 1 and highScorePosition != 11:
        superscript = "st"
    elif highScorePosition % 10 == 2 and highScorePosition != 12:
        superscript = "nd"
    elif highScorePosition % 10 == 3 and highScorePosition != 13:
        superscript = "rd"
    else:
        superscript = "th"

    return render_template("NewHighScore.html",
                           page_title = "New High Score",
                           name_entered = session.get("lastPlayer"), 
                           home_url = url_for("show_home_page"),
                           score_list = listOfAllHighScores[0:10],
                           ranking_position = highScorePosition,
                           super_script = superscript,
                           play_url = url_for("start_new_game"), )

@app.route("/viewhighscores")
def view_high_scores():
    listOfAllHighScores = getSortedHighScoresList()
    return render_template("ViewTopScorersList.html",
                           page_title = "View the Top 10 Fastest Players",
                           home_url = url_for("show_home_page"),
                           score_list = listOfAllHighScores[0:10], )
    
app.config['SECRET_KEY'] = 'ihopethisisnotCHRISsblood'
#if __name__ == "__main__":
#    app.run(processes = 4)
app.run(debug = True)


    
