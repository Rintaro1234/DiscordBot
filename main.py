from tokenize import Intnumber
import discord 
import json
import requests
import romkan
import wave
import os
import threading

from discord.ext import commands

intents = discord.Intents.all() 
bot = commands.Bot(intents=intents)
voice:discord.VoiceChannel
ChatChannel:discord.channel
QueueSound = []

@bot.event
async def on_ready():
  print("logged in as " + bot.user.name)
  t1 = threading.Thread(target=playSound)
  t1.start()

@bot.event
async def on_message(message):
    if message.author.bot != True:
        global ChatChannel
        ChatChannel = message.channel
        #generate_wav(message.content)
        #bot.voice_clients[0].play(discord.FFmpegPCMAudio(executable="C:\\Program Files\\ffmpeg-master-latest-win64-gpl-shared\\bin\\ffmpeg.exe", source="./audio.wav"))
        #await ChatChannel.send(message.content)

isConnect:bool = False
voiceClient:discord.VoiceClient

@bot.event
async def on_voice_state_update(data, before, after):
    global isConnect
    global voiceClient
    if before.channel != after.channel:
        botRoom = bot.get_channel(951458703847088140)
        voiceRoom = bot.get_channel(950376706731020311)
        if isConnect != True and data.bot != True:
            voiceClient = await voiceRoom.connect()
            isConnect = True

        members = voiceRoom.members
        for i in range(len(members)):
            if members[i].bot != True:
                break
            if i == len(members) - 1:
                await voiceRoom.guild.voice_client.disconnect()
                isConnect = False
                return

        audiopath = "./audiosources/" + str(data.id) + ".wav"
        if os.path.isfile(audiopath) != True:
            voiceText = romkan.to_katakana(data.name)
            generate_wav(voiceText, filepath=audiopath)

        # 入室通知
        if after.channel != None and after.channel.id == voiceRoom.id and data.name != bot.user.name:
            enterpath = "./audiosources/enter" + str(0) + ".wav"
            QueueSound.insert(0, audiopath)
            QueueSound.insert(0, enterpath)
            #voiceClient.play(discord.FFmpegPCMAudio(executable="C:\\Program Files\\ffmpeg-master-latest-win64-gpl-shared\\bin\\ffmpeg.exe", source=audiopath))
            #while(voiceClient.is_playing()): pass
            #voiceClient.play(discord.FFmpegPCMAudio(executable="C:\\Program Files\\ffmpeg-master-latest-win64-gpl-shared\\bin\\ffmpeg.exe", source=enterpath))
            await botRoom.send(data.name + "が現れた！")

        # 退出通知
        if before.channel != None and before.channel.id == voiceRoom.id and data.name != bot.user.name:
            exitpath = "./audiosources/exit" + str(0) + ".wav"
            QueueSound.insert(0, audiopath)
            QueueSound.insert(0, exitpath)
            #voiceClient.play(discord.FFmpegPCMAudio(executable="C:\\Program Files\\ffmpeg-master-latest-win64-gpl-shared\\bin\\ffmpeg.exe", source=audiopath))
            #while(voiceClient.is_playing()): pass
            #voiceClient.play(discord.FFmpegPCMAudio(executable="C:\\Program Files\\ffmpeg-master-latest-win64-gpl-shared\\bin\\ffmpeg.exe", source=exitpath))
            await botRoom.send(data.name + "が退出しました。")

# 音キューの再生
def playSound():
    t = threading.Timer(0.5, playSound)
    t.start()
    if len(QueueSound) != 0 and voiceClient.is_playing() != True and voiceClient.is_connected():
        # windows voiceClient.play(discord.FFmpegPCMAudio(executable="C:\\Program Files\\ffmpeg-master-latest-win64-gpl-shared\\bin\\ffmpeg.exe", source=QueueSound[len(QueueSound) - 1]))
        voiceClient.play(discord.FFmpegPCMAudio(source=QueueSound[len(QueueSound) - 1]))
        QueueSound.pop()   


# 音声ファイルの作成
def generate_wav(text, speaker=2, filepath='./audiosources/audio.wav'):
    response2 = requests.post("https://api.su-shiki.com/v2/voicevox/audio/?key=U_4463J7F-B9f-5&speaker=" + str(speaker) + "&pitch=0&intonationScale=1&speed=1&text=" + text)

    wf = wave.open(filepath, 'wb')
    wf.setnchannels(1)
    wf.setsampwidth(2)
    wf.setframerate(24000)
    wf.writeframes(response2.content)
    wf.close()

bot.run(DISCORD_BOT_TOKEN)