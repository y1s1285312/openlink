from flask import Flask,request
from flask_socketio import SocketIO
import logging
import pymysql
import json
import pygame
import threading
import json
import gspeech
import time



con = pymysql.connect(host='dementia.openlink.kr', user='admin', password='Opendb1234!@',
                       db='openlink', charset='utf8') # 한글처리 (charset = 'utf8')


app = Flask(__name__)
app.config['SECRET_KEY'] = 'mysecret'



socketio = SocketIO(app, cors_allowed_origins='*')


app.debug = True
#app.host = '0.0.0.0'
app.port = 5000
logging.basicConfig(level=logging.ERROR)

pygame.mixer.pre_init(24000)
pygame.init()
testing = False
exit_event = threading.Event()

test = []
patients= {}

words = {}
datas = {}
stop=False

with open('./testData.json', 'r') as f:
    datas = json.load(f)
    word = []
    for x in datas[0]['questions']:
        word.append(x['content']['word'])
    words['words'] = word
    word = []
    for x in datas[10]['questions']:
        word.append(x['content']['word'])
    words['single']=word

anilist = '''
1. 고양이 2. 강아지
3. 거북이 4. 토끼
5. 뱀 6. 사자
7. 호랑이 8. 표범
9. 치타 10. 하이에나
11. 기린 12. 코끼리
13. 코뿔소 14. 하마
15. 악어 16. 펭귄
17. 부엉이 18. 올빼미
19. 곰 20. 돼지
21. 소 22. 닭
23. 독수리 24. 타조
25. 고릴라 26. 오랑우탄
27. 침팬지 28. 원숭이
29. 코알라 30. 캥거루
31. 고래 32. 상어
33. 칠면조 34. 직박구리
35. 쥐 36. 청설모
37. 메추라기 38. 앵무새
39. 삵 40. 스라소니
41. 판다 42. 오소리
43. 오리 44. 거위
45. 백조 46. 두루미
47. 고슴도치 48. 두더지
49. 우파루파 50. 맹꽁이
51. 너구리 52. 개구리
53. 두꺼비 54. 카멜레온
55. 이구아나 56. 노루
57. 제비 58. 까지
59. 고라니 60. 수달
61. 당나귀 62. 순록
63. 염소 64. 공작
65. 바다표범 66. 들소
67. 박쥐 68. 참새
69. 물개 70. 바다사자
71. 살모사 72. 구렁이
73. 얼룩말 74. 산양
75. 멧돼지 76. 카피바라
77. 바다코끼리 78. 도롱뇽
79. 북극곰 80. 퓨마
81. 미어캣 82. 코요테
83. 라마 84. 딱따구리
85. 기러기 86. 비둘기
87. 스컹크 88. 아르마딜로
89. 돌고래 90. 까마귀
91. 매 92. 낙타
93. 여우 94. 사슴
95. 늑대 96. 재규어
97. 알파카 98. 양
99. 다람쥐 100. 담비
'''.split()[1::2]
anilist = list(map(lambda x : x.strip(),anilist))
    





@app.route("/")
def main():
     return ' '


@socketio.on('connect')
def on_connect(client):
    print('conn',client)

@socketio.on('disconnect')
def disconnect():
    cur = con.cursor(pymysql.cursors.DictCursor)
    print('discon',request.sid)
    
    if request.sid in patients:
        sql = "DELETE FROM TN_Scheduler WHERE phoneNumber='{}'".format(patients[request.sid])
        cur.execute(sql)
        con.commit()
        return


@socketio.on('patientJoin')
def checkpatient(data):
    
    phone = data['phoneNumber']
    cur = con.cursor(pymysql.cursors.DictCursor)
    sql = "SELECT patCd,NAME,BIRTH FROM TN_CM_TRGTER_INFO WHERE TEL_NO_1='{}' and TEL_NO_2='{}' and TEL_NO_3='{}'".format(phone[:3],phone[3:7],phone[7:])
    cur.execute(sql)
    # 데이타 Fetch
    rows = cur.fetchone()
    print(rows,request.sid)

    if rows :
        socketio.emit('patientJoin',True)
        sql = "INSERT INTO TN_Scheduler (patCd,NAME,phoneNumber,BIRTH) VALUES (%s,%s,%s,%s)"
        val = (rows['patCd'],rows['NAME'],phone,rows['BIRTH'])
        cur.execute(sql,val)
        con.commit()
        patients[request.sid] = phone
    else :
        socketio.emit('patientJoin',False)


@socketio.on('doctorJoin')
def checkdoctor(data):
    print('doctorJoin',request.sid)
    cur = con.cursor(pymysql.cursors.DictCursor)
    sql = "SELECT USER_ID FROM TN_CM_USER_INFO WHERE LOGIN_ID='{}'".format(data['id'])
    cur.execute(sql)
    # 데이타 Fetch
    rows = cur.fetchone()
    
    userid = rows['USER_ID']
    #print(patients[data['phoneNumber']])
    if rows:
        socketio.emit('doctorJoin',True)
    

@socketio.on('patientInfo')
def getPatientInfo():
    print('patientInfo')
    
    cur = con.cursor(pymysql.cursors.DictCursor)
    sql = "SELECT patCd,NAME,phoneNumber,BIRTH FROM TN_Scheduler"
    cur.execute(sql)
    # 데이타 Fetch
    rows = cur.fetchall()
    res = json.dumps(rows)
    # 전체 rows
    socketio.emit('patientInfo',res)


@socketio.on('startTest')
def startTest(index):
    print('start Test')
    info = datas[index]
    #print(info)
    socketio.emit('startTest',{'testType':info['type'],'narration':info['narration']})

@socketio.on('testFinished')
def testFinished():
    socketio.emit('testFinished',True)


@socketio.on('startWords')
def startWords(data):
    info = datas[0]
    print('start words',data,info)
    
    gsp = gspeech.Gspeech()
    stop = False
    findwords = []
    word = words[data].copy()
    print(word)

    @socketio.on('stopWords')
    def stopWords():
        stop = True
        

    while True:
        # 음성 인식 될때까지 대기 한다.
        stt = gsp.getText()
        finded = []
        
        stt = stt.strip()
        print(stt)
        time.sleep(0.01)
        for r in word:
            if (r in stt) and not (r in finded):
                wordsResult = {'response':{'index':str(word.index(r)+1),
                'phase':0,
                'result':{'response':r,'score':1}}}
                #print(wordsResult)
                
                if  not stop:
                    print('emit result')
                    socketio.emit('wordsResult',wordsResult)
                    
                findwords.append(word.index(r))
                finded.append(r)
       
        for x in findwords:
            word[x] = '!@'

        if (not stt) or stop:
            print('stop')
            break

    print('end startwords')


@socketio.on('startSingleWords')
def startSingleWordsMemory(data):
    print('startSingleWordsMemory',data)
    
    gsp = gspeech.Gspeech()

    stop = False
    findwords = []
    word = words['single'].copy()
    print(word)
    order = 1
    
    @socketio.on('stopSingleWords')
    def stopSingleWords():
        stop = True
        

    while True:
        # 음성 인식 될때까지 대기 한다.
        

        stt = gsp.getText()
        finded = []

        stt = stt.strip()
        print(stt)
        time.sleep(0.01)
        for r in word:
            if (r in stt) and not (r in finded):
                wordsResult = {'response':{'index':str(word.index(r)+1),
                'phase':data,
                'result':{'order':order,'word':r,'score':1}}}
                #print(wordsResult)
                
                if  not stop:
                    print('emit result')
                    socketio.emit('SingleWordsResult',wordsResult)
                    print('inc order')
                    order +=1
                
                findwords.append(word.index(r))
                finded.append(r)
                break
        for x in findwords:
            word[x] = '!@'

        if (not stt) or stop:
            print('stop')
            break

    print('end startSingleWords')
    

@socketio.on('startSM')
def startSM(data):

    index = data['index']
    correct = data['correct']

    corrects = ['일','이','삼','사','오','육','칠','팔','구','십']

    print('start SM')
    print(index,correct)

    
    gsp = gspeech.Gspeech()
    
    stop = False

    @socketio.on('stopSM')
    def stopSM():
        stop = True
        
        
    while True:
        # 음성 인식 될때까지 대기 한다.
        stt = gsp.getText()
        finded = []
        
        stt = stt.strip()
        print(stt)
        time.sleep(0.01)
        if stt in [correct,corrects[int(correct)-1]]:
            print('clear')
            stop = True
            Result = {'response':{'index':index,
                'phase':0,
                'result':{'response':int(correct) ,'score':1}}}
                #print(wordsResult)
            print('emit result')
            socketio.emit('SMResult',Result)
            
        if (not stt) or stop:
            print('stop')
            break
        

    print('end SM')


@socketio.on('startSMM')
def startSMM(data):

    index = data['index']
    correct = data['correct']

    print('start SMM')
    print(index,correct)

    gsp = gspeech.Gspeech()
    
    stop = False

    @socketio.on('stopSMM')
    def stopSM():
        stop = True
        
        
    while True:
        # 음성 인식 될때까지 대기 한다.
        stt = gsp.getText()
        stt = stt.strip()
        print(stt)
        time.sleep(0.01)
        if stt == '예':
            stop = True
            Result = {'response':{'index':index,
                'phase':0,
                'result':{'response':True ,'score':1*(correct == 0)}}}
                #print(wordsResult)
            print('emit result')
            socketio.emit('SMMResult',Result)

        elif stt == '아니오' or stt=='아니요':
            stop = True
            Result = {'response':{'index':index,
                'phase':0,
                'result':{'response': False,'score':1*(correct == 1)}}}
                #print(wordsResult)
            print('emit result')
            socketio.emit('SMMResult',Result)
        

        if (not stt) or stop:
            print('stop')
            break
        

    print('end SMM')


@socketio.on('startStickMemory')
def startStickMemory(element):
    print(element)
    info = datas[9].copy()
    index = element['index']
    correct = element['content']['correct']
    print(info)
    socketio.emit('startNarration',{'testType':info['type'],'narration':info['narration'],'questions':element})
    
    gsp = gspeech.Gspeech()
    
    stop = False

    @socketio.on('stopStickMemory')
    def stopStickMemory():
        stop = True

    while True:
        # 음성 인식 될때까지 대기 한다.
        stt = gsp.getText()
        stt = stt.strip()
        print(stt)
        time.sleep(0.01)
        if stt == '예':
            stop = True
            Result = {'response':{'index':index,
                'phase':0,
                'result':{'response':True ,'score':1*(correct == '0')}}}
                #print(wordsResult)
            print('emit result')
            socketio.emit('stickMemoryResult',Result)

        elif stt == '아니오' or stt=='아니요':
            stop = True
            Result = {'response':{'index':index,
                'phase':0,
                'result':{'response': False,'score':1*(correct == '1')}}}
                #print(wordsResult)
            print('emit result')
            socketio.emit('stickMemoryResult',Result)
        

        if (not stt) or stop:
            print('stop')
            gsp.mic.Pause()
            break

@socketio.on('startShapeColor')
def startShapeColor(element):
    print(element)
    @socketio.on('stopShapeColor')
    def stopShapeColor():
        stop = True

    info = datas[13].copy()
    index = element['index']
    if int(index) < 0 :
        index = '0' 
    word = element['content']['word']
    
    socketio.emit('startNarration',{'testType':info['type'],'narration':info['narration'],'questions':element})
    
    wordlist = ['무', '수박', '귤', '호두', '당근', '깻잎', '연근', '오이', '고추', '땅콩', '말', '토끼', '다람쥐', '금붕어', '돼지', '오리']
    corlist = [1,2,1,1,2,2,2,1,1,2,1,2,2,1,2,1]
    numberlist = [['1','일'],['2','이']]
    cor = numberlist[corlist[int(index)]-1]

    gsp = gspeech.Gspeech()
    stop = False

    
    while True:
        # 음성 인식 될때까지 대기 한다.
        stt = gsp.getText()
        stt = stt.strip()
        print(stt)
        time.sleep(0.01)
        
        
        print('go')
        stop = True
        Result = {'response':{'index':index if int(index) > 0 else str(int(index)-1),
            'phase':0,
            'result':{'word': stt,'imageScore':1*((cor[0] in stt) or (cor[1] in stt)),
            'nameScore':1*(word in stt)}}}
            #print(wordsResult)
        print('emit result')
        socketio.emit('shapeColorResult',Result)
        

        if (not stt) or stop:
            print('stop')
            gsp.pauseMic()
            break

@socketio.on('startwordFluencyTest')
def startShapeColor(element):
    start = time.time()

    #print(element)
    gsp = gspeech.Gspeech()
    seq = ['0 ~ 15 seconds', '16 ~ 30 seconds', '31 ~ 45 seconds', '46 ~ 60 seconds']
    #print(anilist)
    @socketio.on('stopwordFluency')
    def stopwordFluency():
        global stop
        stop = True

    while True:
        if stop:
            print('stop')
            break
        # 음성 인식 될때까지 대기 한다.
        stt = gsp.getText()
        stt = stt.strip()
        time.sleep(0.01)
        
        print(stt)
        score = 0
        corlist = []
        for x in stt.split():
            if x in anilist:
                score +=1
                corlist.append(x)
        if score >0:
            endtime = int(time.time() - start)
            index = str(int(endtime/15)+1)
            
            print(endtime,score)
            
            Result = {'response':{
                'index':index,
                'phase':0,
                'result':{'word': ' '.join(corlist),'score':score}}}
            print('emit result')
            socketio.emit('wordFluencyResult',Result)
    
        

cors_calTest= {'add':[[40,80,150],[30,70,120]],
'sub':[[10,40,90],[20,50,70]],'mult':[[300,60,250],[200,40,150]],
'div':[['네','다섯','아홉'],['세','세','일곱']]}
@socketio.on('startcalTest')
def startcalTest(element):
    #print(element)
    
    print('startCal')
    stop=False
    gsp = gspeech.Gspeech()
    @socketio.on('stopCalTest')
    def stopCalTest():
        print('stopCalTest')
        stop = True
    

    ttype = element[0]
    index = element[1]

    cor = cors_calTest[ttype][int(index)-1][element[2]]

    #print(ttype,index)
    #print(cor)

    while True:
        if stop:
            print('stop')
            break
        # 음성 인식 될때까지 대기 한다.
        
        stt = gsp.getText()
        stt = stt.strip()
        time.sleep(0.01)
        
        print(stt)
        
        Result = {'response':{
            'index':'-'.join([ttype,index,str(element[2]+1)]),
            'phase':0,
            'result':{'response':stt ,'score':1*(str(cor) in stt)}}}
        print('emit result')
        
        socketio.emit('calResult',Result)
        socketio.emit('next',[ttype,index,element[2]])
        break
    gsp.pauseMic()
    print('endCalTest')


numbersetdata = datas[5]['questions'].copy()

cell = []
cells = [[],[]]
for x in numbersetdata:
    cells[0].append(x['content']['leftSet'])
    cells[1].append(x['content']['rightSet'])

nas=[]
na = {'narration':'여기 맨 밑줄에 칸마다 숫자들이 적혀있습니다. 각  칸에 적힌 숫자를 2,1,3 이런 식으로 한 개씩만 읽으십시오. 한 번 해보세요. 자, 이제 제가 시작하면 여기 처음부터 끝까지 정확하면서도 최대한 빠르게 각 칸에 적힌 숫자를 말해보세요. 시작.',
'cells' : cells[0]}
nas.append(na)
na = {'narration':'이번에는 각 칸에 적힌 수자의 개수를 말씀해 보십시오. 한 개, 두 개, 세 개로 세지 마시고 숫자가 한 개 있으면 1, 두 개 있으면 2 이렇게 한 번 해보세요. 잘했습니다. 자, 이제 제가 시작하면 여기 처음부터 끝까지 정확하면서도 최대한 빠르게 각 칸에 몇 개의 숫자가 적혀있는지, 그 개수를 말씀해보십시오. 시작.',
'cells' : cells[1]}
nas.append(na)
numcorlist = [['1','일'],['2','이'],['3','삼']]
@socketio.on('startNumberSet')
def startNumberSet(data):
    stop=False

    

    gsp = gspeech.Gspeech()
    @socketio.on('stopnumSetTest')
    def stopnumSetTest():
        print('stopnumSetTest')
        stop = True
    questions = numbersetdata[data[1]]
    print(questions,data)
    #print(nas[data[0]])
    cors = []
    cors.append(list(set(list(questions['content'].values())[0]))[0])
    cors.append(len(list(questions['content'].values())[1]))
    print(cors)

    socketio.emit('startNarration',{'testType':'numbersSet',
    'narration':nas[data[0]],
    'questions':questions})

    while True:
        if stop:
            print('stop')
            break
        # 음성 인식 될때까지 대기 한다.
        
        stt = gsp.getText()
        stt = stt.strip()
        time.sleep(0.01)
        
        print(stt)
        Result = {'response':{
            'index':questions['index'],
            'phase':data[0],
            'result':{'response':stt ,'score':1*(str(numcorlist[cors[data[0]]-1]) in stt)}}}
        print('emit result')
        
        socketio.emit('numbersetResult',Result)
        break
    gsp.pauseMic()
    print('endnumTest')

    
    




if __name__ == '__main__':
    socketio.run(app)
