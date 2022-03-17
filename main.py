from pickle import FALSE, TRUE
from pickletools import TAKEN_FROM_ARGUMENT8U
from tokenize import Intnumber
import discord 
import json
import requests
import romkan
import wave
import os
import threading
import psycopg2
import re

from discord.ext import commands

intents = discord.Intents.all() 
bot = commands.Bot(intents=intents, command_prefix="$")
DATABASE_URL = os.environ['DATABASE_URL']
QueueSound = []

@bot.event
async def on_ready():
  print("logged in as " + bot.user.name)
  t1 = threading.Thread(target=playSound)
  t1.start()

isConnect:bool = False
voiceClient:discord.VoiceClient

@bot.event
async def on_voice_state_update(data, before, after):
    global isConnect
    global voiceClient
    if before.channel != after.channel:
        #デバック用
        #botRoom = bot.get_channel(950397520859758642)
        #voiceRoom = bot.get_channel(936920395116843051)
        #実装用
        botRoom = bot.get_channel(951458703847088140)
        voiceRoom = bot.get_channel(950376706731020311)
        # 音声チャットに入っていなかったら入場する
        if isConnect != True and data.bot != True:
            voiceClient = await voiceRoom.connect()
            isConnect = True

        # Bot以外の人が誰かいるか？
        members = voiceRoom.members
        for i in range(len(members)):
            if members[i].bot != True:
                break # 人がいたらそのまま接続する
            if i == len(members) - 1:
                await voiceRoom.guild.voice_client.disconnect()
                isConnect = False # 人がいなかったら退出する
                return

        #その人の音源ファイルがあるか？
        audiopath = "./audiosources/" + str(data.id) + ".wav"
        if os.path.isfile(audiopath) != True:
            # データベースにその人の名前が登録されているかの確認
            with psycopg2.connect(DATABASE_URL) as conn:
                with conn.cursor() as curs:
                    curs.execute('SELECT * FROM username')
                    isContained = False
                    # データベースにその人のIDがあるかチェック
                    for row in curs:
                        if row[0] == str(data.id):
                            # 含まれていたら登録された名前でID作成
                            generate_wav(row[1], filepath=audiopath)
                            isContained = True
                            break
                    # 含まれていなかったら新規登録
                    if isContained == False:
                        curs.execute("INSERT INTO username(id, name) VALUES(%s, %s)", (data.id, data.name))
                        generate_wav(data.name, filepath=audiopath)

        # 入室通知
        if after.channel != None and after.channel.id == voiceRoom.id and data.bot != True:
            enterpath = "./audiosources/enter" + str(0) + ".wav"
            # 音声再生のキューを入れる
            QueueSound.insert(0, audiopath)
            QueueSound.insert(0, enterpath)
            # 通知
            await botRoom.send(data.name + "が現れた！")

        # 退出通知
        if before.channel != None and before.channel.id == voiceRoom.id and data.bot != True:
            exitpath = "./audiosources/exit" + str(0) + ".wav"
            # 音声再生のキューを入れる
            QueueSound.insert(0, audiopath)
            QueueSound.insert(0, exitpath)
            # 通知
            await botRoom.send(data.name + "が退出しました。")

# 音声の手動入力
@bot.command()
async def set(ctx, arg):
    path="./audiosources/" + str(ctx.author.id) + ".wav"
    # データベースにその人の名前が登録されているかの確認
    with psycopg2.connect(DATABASE_URL) as conn:
        with conn.cursor() as curs:
            curs.execute('SELECT * FROM username')
            isContained = False
            # データベースにその人のIDがあるかチェック
            for row in curs:
                if row[0] == str(ctx.author.id):
                    # すでに作成済みだったら更新する
                    curs.execute("UPDATE username SET name = %s WHERE id = %s", (arg, str(ctx.author.id)))
                    isContained = True
                    break
            # 含まれていなかったら新規登録
            if isContained == False:
                curs.execute("INSERT INTO username(id, name) VALUES(%s, %s)", (str(ctx.author.id), arg))

    # 名前作成
    generate_wav(arg, filepath=path)
    
    await ctx.send("あなたの名前を「" + arg + "」で生成しました！")
    await ctx.send(file=discord.File(path))

# 音声があるかの確認
@bot.command()
async def check(ctx):
    with psycopg2.connect(DATABASE_URL) as conn:
        with conn.cursor() as curs:
            curs.execute('SELECT * FROM username')
            isContained = False
            # データベースにその人のIDがあるかチェック
            for row in curs:
                if row[0] == str(ctx.author.id):
                    # すでに作成済みだったら更新する
                    await ctx.send("あなたの名前は「" + row[1] + "」で登録されています！")
                    isContained = True
                    break
            # 含まれていなかったら新規登録
            if isContained == False:
                await ctx.send("あなたの名前は登録されていません...")
                return
    path="./audiosources/" + str(ctx.author.id) + ".wav"
    if os.path.isfile(path) == True:
        await ctx.send(file=discord.File(path))
            
# 音キューの再生
def playSound():
    t = threading.Timer(0.5, playSound)
    t.start()
    if len(QueueSound) != 0 and voiceClient.is_playing() != True and voiceClient.is_connected():
        voiceClient.play(discord.FFmpegPCMAudio(source=QueueSound[len(QueueSound) - 1]))
        QueueSound.pop() 

# 音声ファイルの作成
def generate_wav(text, speaker=2, filepath='./audiosources/audio.wav'):
    text = romkan.to_katakana(text)
    text = text.replace('0', 'ゼロ').replace('1', 'イチ').replace('2', 'ニ').replace('3', 'サン').replace('4', 'ヨン').replace('5', 'ゴー').replace('6', 'ロク').replace('7', 'ナナ').replace('8', 'ハチ').replace('9', 'キュウ')
    response2 = requests.post("https://api.su-shiki.com/v2/voicevox/audio/?key=" + os.environ['VoiceToken'] + "&speaker=" + str(speaker) + "&pitch=0&intonationScale=1&speed=1.0&text=" + text)

    wf = wave.open(filepath, 'wb')
    wf.setnchannels(1)
    wf.setsampwidth(2)
    wf.setframerate(24000)
    wf.writeframes(response2.content)
    wf.close()

bot.run(os.environ['TOKEN'])