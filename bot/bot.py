import os
import logging
import telegram
import time
from datetime import datetime
from telegram.ext import CommandHandler, Updater, MessageHandler, Filters
from answers import greetAnswers, thanksAnswers, pleaseAnswers
from webScrapping import weather, findJobs
import instaloader
from getDB import *

logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s," 
)
logger = logging.getLogger()

L = instaloader.Instaloader(download_comments=False, max_connection_attempts=9, post_metadata_txt_pattern=None, save_metadata=False, download_video_thumbnails=False, download_geotags=False, filename_pattern="{shortcode}")#init instaloader

"""Agregar:
-Buscar empleos en computrabajo y devolver link (LISTO)
-Crear base de datos con una tabla que tenga el horario de este semestre(Listo)
-Crear tabla en la base de datos donde pueda agregar recordatorios con fecha, la descripcion de la actividad, tipo de actividad(Listo)
-Dar ultimas noticias de videojuegos(LISTO)
-Dar ultimas noticias de colombia y/o el mundo (instaloader)(LISTO)
-solicitar contraseña para informacion delicada
-No funciona el clima
-instalar todas las liberias que se utiliza con pipenv y crear otro proyecto de heroku(LISTO)
-cambiar la funcionalidad de noticias para que no sea por hora (LISTO)
-enviar correos desde el bot
-Agregar funcionalidades con la base de datos, hacer pruebas con el bot desmontado en heroku y la db en localhost (listo)
-subir la db a la nube a algun servicio gratuito"""


TOKEN = os.getenv("TOKEN")

def ping(update, context):
    bot = context.bot
    chatId = update.message.chat_id
    logger.info(f"El bot funciona!!")
    bot.sendMessage(chat_id=chatId, text="pong")

def getPosts(theme):# get posts using instaloader from keyword 'theme'    
    isVideo = []
    postUsernames = []
    postShortcodes = []
    postCaptions = []

    if 'juego' in theme:
        PROFILES = ["checkandplay", "instantgaminges", "levelupcom", "3djuegos"]
    elif 'pais' in theme:
        PROFILES =["eltiempo", "revistasemana", "elespectador", "elcolombiano"]

    try:
        for PROFILE in PROFILES:
            logger.info(f'Profile = {PROFILE}')            
            profile = instaloader.Profile.from_username(L.context, PROFILE) #connect with profile
            logger.info('Profile loaded')
            count = 0
            for post in profile.get_posts():
                count += 1                                
                download = L.download_post(post, PROFILE)#download post
                logger.info('Download complete')
                if download is True:
                    video = post.is_video #verify if is a video
                    postUsernames.append(post.owner_username) #get post values
                    postShortcodes.append(post.shortcode)
                    postCaptions.append(post.caption)
                    if video is True:
                        isVideo.append(True)                                                        
                    else:
                        isVideo.append(False)                          
                                                                                        
                if count == 2: #get the last two posts
                    break
        logger.info('Next profile')
    except:
        pass

    return isVideo, postUsernames, postShortcodes, postCaptions #send listo with of all of posts info found

def getId(text):
    #user send the keyword with the id in '', in thi method ill get that id
    text = text.replace(" ", "")
    text = text.split(",")    
    if len(text) == 1:
        id = None
    else:
        id = text[1]

    return id

def echo(update, context): #obtener el mensaje que envio el usuario e identificar palabra clave para responderle con lo que solicita   
    bot = context.bot
    chatId = update.message.chat_id
    updateText = getattr(update, "message", None)
    msgId = updateText.message_id
    text = update.message.text
    text = text.lower() #convertir todo el texto en minuscula

    if "hola" in text:
        answer = greetAnswers()
        bot.sendMessage(chat_id=chatId, text=answer)
    
    if 'favor' in text:
        answer = pleaseAnswers()
        bot.sendMessage(chat_id=chatId, text=answer)

    if "clima" in text:
        try:
            todayWeather = weather()
            bot.sendMessage(chat_id=chatId, parse_mode="HTML", text=f"<b>Este es el clima de hoy Yeison:</b>\n\n{todayWeather}")
        except:
            bot.sendMessage(chat_id=chatId, text="Lo siento por ahora esta funcionalidad no está disponible 😔")

    if "gracias" in text:
        answer = thanksAnswers()
        bot.sendMessage(chat_id=chatId, text=answer)

    if "trabajo" in text:        
        try:
            text = text.split(",") #split the sentence and get the desired work for look
            text = text[1] #get desired work into ' '
            listJobsTittles, hyperlinks, companies, publishTimes, workSites = findJobs(text) #get lists with jobs info about the desired work            
            bot.sendMessage(chat_id=chatId, parse_mode= "HTML", text="<b>Aqui estan algunas de las ofertas que pude encontrar:</b>")
            for index in range(len(listJobsTittles)): #get index from all of jobs found
                time.sleep(2)#wait 2 seconds for each job info
                bot.sendMessage(chat_id=chatId,parse_mode="HTML", text=f"<b>Empleo:</b> {listJobsTittles[index]}\n<b>Empresa:</b> {companies[index]}\n<b>Lugar:</b> workSites[index]\n<b>Fecha de publicación:</b> {publishTimes[index]}\n\n<b>Link:</b> {hyperlinks[index]}")  
        except Exception as e:
            bot.sendMessage(chat_id=chatId, text=f"{e} Lo siento por ahora esta funcion no funciona :C")

    if "noticia" in text and 'juego' in text:
        answer = pleaseAnswers()
        bot.sendMessage(chat_id=chatId, text=answer)#send message before of collect posts
        try:
            isVideo, postUsernames, postShortcodes, postCaptions = getPosts('juego') #get lists with posts info about 'juegos'
            for index in range(len(isVideo)): #loop each posts index
                if isVideo[index] is True:
                    try:
                        with open(postUsernames[index]+'/'+postShortcodes[index]+'.mp4', 'rb') as f:#get the downloaded post in the getPosts() method
                            bot.send_video(chat_id=chatId, video=f)
                            if postCaptions[index] == None: #if the post has not description
                                bot.sendMessage(chat_id=chatId, parse_mode='HTML', text=f'<b>{postUsernames[index]}:</b> None')
                            else: #send message with post description
                                bot.sendMessage(chat_id=chatId, parse_mode='HTML', text=f'<b>{postUsernames[index]}:</b> {postCaptions[index]}')
                    except:
                        pass
                else: #is an image
                    try:
                        with open(postUsernames[index]+'/'+postShortcodes[index]+'.jpg', 'rb') as f:
                            bot.send_photo(chat_id=chatId, photo=f)
                            if postCaptions[index] == None: #if the post has no description
                                bot.sendMessage(chat_id=chatId, parse_mode='HTML', text=f'<b>{postUsernames[index]}:</b> None')
                            else: #send message with post description
                                bot.sendMessage(chat_id=chatId, parse_mode='HTML', text=f'<b>{postUsernames[index]}:</b> {postCaptions[index]}')
                    except:
                        pass
            
                time.sleep(2)
        except:
            bot.sendMessage(chat_id=chatId, text="No esta disponible esta funcion")
        
    if "noticia" in text and "pais" in text: #get news about Colombia
        #meter todo en try
        answer = pleaseAnswers()
        bot.sendMessage(chat_id=chatId, text=answer)#send message before of collect posts
        isVideo, postUsernames, postShortcodes, postCaptions = getPosts('pais')
        for index in range(len(isVideo)):
            if isVideo[index] is True:
                try:
                    with open(postUsernames[index]+'/'+postShortcodes[index]+'.mp4', 'rb') as f:
                        bot.send_video(chat_id=chatId, video=f)
                        if postCaptions[index] == None: #if the post has no description
                            bot.sendMessage(chat_id=chatId, parse_mode='HTML', text=f'<b>{postUsernames[index]}:</b> None')
                        else: #send message with post description
                            bot.sendMessage(chat_id=chatId, parse_mode='HTML', text=f'<b>{postUsernames[index]}:</b> {postCaptions[index]}')
                except:
                    pass
            else:
                try:
                    with open(postUsernames[index]+'/'+postShortcodes[index]+'.jpg', 'rb') as f:
                        bot.send_photo(chat_id=chatId, photo=f)
                        if postCaptions[index] == None: #if the post has no description
                            bot.sendMessage(chat_id=chatId, parse_mode='HTML', text=f'<b>{postUsernames[index]}:</b> None')
                        else: #send message with post description
                            bot.sendMessage(chat_id=chatId, parse_mode='HTML', text=f'<b>{postUsernames[index]}:</b> {postCaptions[index]}')
                except:
                    pass
            
            time.sleep(2)

    if "uni" in text:
        meetings = getUniMeetings() #get the tuple with of each meet list
        bot.sendMessage(chat_id=chatId, text="Aqui esta tu horario de universidad:")
        for meet in meetings:
            bot.sendMessage(chat_id=chatId, parse_mode="HTML", text=f"<b>Clase:</b> {meet[1]}\n<b>Dias/horario:</b> {meet[2]}/{meet[3]}\n<b>Link clase</b> {meet[4]}")

    if "elimina" in text and "tarea" in text:
        id = getId(text)
        if id is None:
            bot.sendMessage(chat_id=chatId, text="No ingresaste el codigo de la tarea a borrar")
        else:
            bot.sendMessage(chat_id=chatId, text="Verifica que el id haya sido correcto. Eliminacion en proceso")            
            deleteTask(id)            
            
    if "elimina" in text and "idea" in text:
        id = getId(text)
        if id is None:
            bot.sendMessage(chat_id=chatId, text="No ingresaste el codigo de la idea a borrar")
        else:
            bot.sendMessage(chat_id=chatId, text="Verifica que el id haya sido correcto. Eliminacion en proceso")            
            deleteIdea(id)  

    if "nueva" in text and "tarea" in text:
        text = text.split(",")
        if len(text) != 1:
            insertTask(text[1], text[2])
            bot.sendMessage(chat_id=chatId, text="Se ha agregado la tarea correctamente")
        else:
            bot.sendMessage(chat_id=chatId, text="No has ingresado correctamente el nombre y la descripcion.")

    if "nueva" in text and "idea" in text:
        text = text.split(",")
        if len(text) != 1:
            insertIdea(text[1], text[2])
            bot.sendMessage(chat_id=chatId, text="Se ha agregado la idea correctamente")
        else:
            bot.sendMessage(chat_id=chatId, text="No has ingresado correctamente el nombre y la descripcion.")

    if "ver" in text and "tarea" in text:
        id = getId(text)
        tasks = getTasks(id)

        if id is None:
            bot.sendMessage(chat_id=chatId, text=f"Aqui estan las tareas:")
            for task in tasks:
                bot.sendMessage(chat_id=chatId, parse_mode= "HTML", text=f"<b>id:</b> {task[0]}\n<b>Tarea:</b> {task[1]}")
        else:
            bot.sendMessage(chat_id=chatId, parse_mode="HTML", text=f"<b>Aqui esta la tarea:</b>\n\n<b>Tarea:</b> {tasks[1]}\n<b>Descripción:</b> {tasks[2]}")

    if "ver" in text and "idea" in text:
        id = getId(text)
        ideas = getIdeas(id)

        if id is None:
            bot.sendMessage(chat_id=chatId, text=f"Aqui estan las ideas:")
            for idea in ideas:
                bot.sendMessage(chat_id=chatId, parse_mode= "HTML", text=f"<b>id:</b> {idea[0]}\n<b>Tarea:</b> {idea[1]}")
        else:
            bot.sendMessage(chat_id=chatId, parse_mode="HTML", text=f"<b>Aqui esta la tarea:</b>\n\n<b>Tarea:</b> {ideas[1]}\n<b>Descripción:</b> {ideas[2]}")

    
if __name__ == "__main__":
    mybot = telegram.Bot(token=TOKEN)
    updater = Updater(mybot.token, use_context=True)
    dp = updater.dispatcher

dp.add_handler(CommandHandler("ping", ping))
dp .add_handler(MessageHandler(Filters.text, echo)) #get text from chat

updater.start_polling()
print("BOT IS RUNNING")
updater.idle()