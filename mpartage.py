#!/usr/bin/env python2
# -*-coding:utf-8-*-
# m_partage1.3-hl

import pygtk
pygtk.require("2.0")
import gtk, subprocess, threading, gobject, os, sys
import SimpleHTTPServer, SocketServer
from os import chdir

gobject.threads_init()

PORT = 9900
Handler = SimpleHTTPServer.SimpleHTTPRequestHandler
httpd = SocketServer.TCPServer(("", PORT), Handler)

ip_public = subprocess.Popen("wget -qO- icanhazip.com", shell=True, stdout=subprocess.PIPE)	
lien_de_partage_public = ip_public.communicate()[0].rstrip()
ip_locale = subprocess.Popen("ip addr show $(ip link | grep -m 1 \"state UP\" | awk -F\":\" '{print $2}') | grep inet\  | awk -F\" \" '{print $2}' | awk -F\"/\" '{print $1}'", shell=True, stdout=subprocess.PIPE)	
lien_de_partage_locale = ip_locale.communicate()[0]
listNettoyage = []

class Handler(SimpleHTTPServer.SimpleHTTPRequestHandler):
	serveur_version = '1.0'
	
class Serveur_thread(threading.Thread):
	def __init__(self):
		threading.Thread.__init__ (self)	
	def run(self):
		httpd.serve_forever()

class Systray():
	def __init__(self, window, timer):
		self.window = window
		self.icon = gtk.StatusIcon()
		self.icon.set_from_icon_name('m_partage2')
		self.icon.set_visible(True)
		
		self.icon.connect('activate', self.affiche)
		gobject.timeout_add_seconds(timer, self.show_icons)
		
	def affiche(self, widget):
		self.icon.set_visible(False)
		self.window.show()
		
	def show_icons(self):
		self.icon.set_visible(True)
		
					
class Main():
	
	def motion_cb(self, wid, context, x, y, time):
		'''selection du widget envoi du signal copie'''
		context.drag_status(gtk.gdk.ACTION_COPY, time)
		return True
	    
	def drop_cb(self, wid, context, x, y, time):
	    wid.drag_get_data(context, context.targets[-1], time)
	    return True
	    
	def got_data_cb(self, wid, context, x, y, data, info, time):
		'''Le dossier est déposé dans la fenetre,  deposer'''
		emplacement = data.get_uris()[0].split('file://')[1]
		emplacement = self.m_decode(emplacement)
		try:	
			chdir(emplacement)
			self.creation_page(emplacement)
			self.label.set_text("\n"+emplacement+"\n\nhttp://"+lien_de_partage_locale.rstrip()+":"+str(PORT)+"\n\nhttp://"+lien_de_partage_public+":"+str(PORT)+"\n\n")
		except OSError:
			fichier = os.path.basename(emplacement)
			emplacement = emplacement.rstrip(fichier)
			chdir(emplacement)
			self.label.set_text("\n"+fichier+"\n\nhttp://"+lien_de_partage_locale.rstrip()+":"+str(PORT)+"/"+fichier+"\n\nhttp://"+lien_de_partage_public+":"+str(PORT)+"/"+fichier+"\n\n")
		
		self.label.set_selectable(True)
		context.finish(True, False, time)
		
	def quitter(self, widget, boutonValidation, typePartage, window):
		'''On recupére la valeur des boutons pour s'avoir comment quitter'''
		if boutonValidation.get_active() and typePartage.get_active() == False:
			for fichier in listNettoyage:
				os.remove(fichier)
			httpd.shutdown()
			gtk.main_quit()
		if boutonValidation.get_active() and typePartage.get_active() == True:
			#le bouton garder le partage actif est pas actif on cache la fenetre
			window.hide ()
			Systray(window, 300)	
		else:
			gtk.main_quit()
			
	def evnmt_delete(self, widget, evenement, donnees=None):
		'''empeche la fermeture de la fenetre au clique sur la croix'''
		Systray(widget, 300)
		widget.hide ()
		return True	
					
	def partage(self, widget, boutonValidation):
		'''si le bouton Activer le partage est active on démarre le serveur sinon on le coupe'''
		if widget.get_active():
			serveur =  Serveur_thread()
			serveur.start()	
			boutonValidation.set_label("Partage actif")
		else:
			httpd.shutdown()
			boutonValidation.set_label("Activer le partage")
			if len(listNettoyage) > 0:
				for fichier in listNettoyage:
					os.remove(fichier)
				
	def m_decode(self, emplacement):
		'''Parce que les accents c'est MAL'''
		dic_encodage = {'%C3%A0':'à',  '%C3%A1':'á', '%C3%A2':'â', '%C3%A7':'ç', '%C3%A8':'è', '%C3%A9':'é',
		                '%C3%AA':'ê', '%C3%AB':'ë', '%C3%AE':'î', '%C3%AF':'ï', '%C3%B1':'ñ', '%C3%B2':'ò',
		                '%C3%B3':'ó', '%C3%B4':'ô'} # ça suffit 
		for cle, valeur in dic_encodage.items():
			if cle in emplacement:
				emplacement = emplacement.replace(str(cle), str(valeur))
		return emplacement
		
	def creation_page(self, emplacement):
		'''Fonction qui recupére les fichiers et dossier a partager et créer la page html'''
		liste_images, list_dossiers, list_doc, list_download, list_multimedia = [], [], [], [], []
		liste_fichiers = os.listdir(os.getcwd())
		indexHtml = open(os.getcwd()+"/index.html", 'w')
		indexHtml.write('<html>\n<meta charset="utf-8"/>\n<title>m_partage : le partage facile</title>\n<body  style="background-color:#e1e1e1;color:#222;">\n<a href="../">retour au dossier parent</a>\n<h2>Index des dossiers/fichiers partagés : </h2>\n<hr>\n')
		listNettoyage.append(os.getcwd()+"/index.html")	
		for fichier in liste_fichiers:
			if os.path.isdir(fichier) == True:
				list_dossiers.append(fichier)
				chdir(fichier)
				self.creation_page(emplacement)# Rappel de la fonction pour créer page dans les sous dossiers
			if os.path.splitext(fichier)[1].lower() in ['.jpg', '.png', '.gif', '.jpeg', '.xcf', '.bmp', '.xpm', '.psd', '.psp', '.tif', '.tiff', '.ai', '.aac', '.ico', '.ppm', '.xbm']:
				liste_images.append(fichier)
			if os.path.splitext(fichier)[1].lower() in  ['.mp3', '.flv', '.mp4', '.m4v', '.mpg', '.mpeg', '.m4a', '.wma', '.mov', '.avi', '.mkv', '.ogg', '.ogv', '.ogm', '.wmv', '.wav', '.mid', '.ac3', '.aif', '.aifc', '.aiff', '.divx', '.flac', '.m3u', '.ra', '.rv', '.vob']:
				list_multimedia.append(fichier)
			if os.path.splitext(fichier)[1].lower() in ['.py', '.sh', '.pl', '.rb', '.txt', '.css', '.pdf', '.php', '.odb', '.odc', '.odf', '.odg', '.odp', '.ods', '.odt', '.ott', '.otg', '.oth', '.ots', '.sxw', '.stw', '.fodt', '.uot', '.doc', '.docx', '.dot', '.dotm', '.dotx', '.xml', '.pdb', '.psw', '.ppt', '.pps', '.xhtml', '.html', '.htm', '.rtf', '.ini', '.xls', '.abw', '.c', '.cc', '.cp', '.cpp', '.cs', '.csv', '.cfg', '.h', '.info', '.js', '.jav', '.java', '.latex', '.log', '.old', '.ps', '.rc', '.rdf']:
				list_doc.append(fichier)
			if os.path.splitext(fichier)[1] == '' and  os.path.isfile(fichier) == True:
				list_doc.append(fichier)
			if os.path.splitext(fichier)[1].lower() in ['.deb', '.gnu', '.gz', '.tar', '.tar.gz', '.tgz', '.zip', '.bzip', '.rar', '.bz', '.bz2', '.7z', '.cbr', '.arc', '.arj', '.ark', '.exe', '.run', '.bin', '.ttf', '.bat', '.iso', '.torrent']:
				list_download.append(fichier)
						
		if len(list_dossiers) != 0:
			indexHtml.write('<h4>dossier(s) /</h4>\n<ul>\n')
			for dossier in list_dossiers:
				indexHtml.write("<li><a href='"+dossier+"'>"+dossier+"</a></li>\n")
			indexHtml.write('</ul>\n<hr>\n')
						 
		if len(liste_images) != 0:
			indexHtml.write('<h4>image(s) /</h4>\n<ul>\n')
			for image in liste_images:
				indexHtml.write("<li><a href='"+image+"'>"+image+"</a></li>\n")
			indexHtml.write('</ul>\n<hr>\n')
			
		if len(list_multimedia) != 0:
			indexHtml.write('<h4>multimedia /</h4>\n<ul>\n')
			for media in list_multimedia:
				indexHtml.write("<li><a href='"+media+"'>"+media+"</a></li>\n")
			indexHtml.write('</ul>\n<hr>\n')
			
		if len(list_download) != 0:
			indexHtml.write('<h4>téléchargement /</h4>\n<ul>\n')
			for down in list_download:
				indexHtml.write("<li><a href='"+down+"'>"+down+"</a></li>\n")
			indexHtml.write('</ul>\n<hr>\n')
			
		if len(list_doc) != 0:
			indexHtml.write('<h4>document(s) /</h4>\n<ul>\n')
			for doc in list_doc:
				indexHtml.write("<li><a href='"+doc+"'>"+doc+"</a></li>\n")
			indexHtml.write('</ul>\n<hr>\n')	
			
		indexHtml.write('<p align=center ><FONT size="2"><b>mpartage</b> par manon@<a href="http://www.shovel-crew.org">Shovel-crew.org</a> pour <a href="http://handylinux.org">handylinux</a></FONT></p><hr>\n</body>\n</html>')
		indexHtml.close()
		chdir(emplacement)
		
	def __init__(self):
		
		window = gtk.Window()
		window.set_size_request(450, 250)
		window.connect('delete_event', self.evnmt_delete, window)
		
		vBox = gtk.VBox()
		cadre = gtk.Frame(label="Dossier Partagé")
		cadre.set_label_align(0.0, 0.5)
		cadre.set_shadow_type(gtk.SHADOW_IN)
		self.label = gtk.Label("deposer ici le dossier \nque vous voulez partager")
		self.label.drag_dest_set(0, [], 0)
		self.label.connect('drag_motion', self.motion_cb)
		self.label.connect('drag_drop', self.drop_cb)
		self.label.connect('drag_data_received', self.got_data_cb)
		cadre.add(self.label)
		vBox.pack_start(cadre, True, True, 10)
		
		option = gtk.HBox()
		boutonValidation = gtk.CheckButton('Activer le Partage')
		typePartage = gtk.CheckButton("Laisser le partage Actif") 
		boutonValidation.connect("clicked", self.partage, boutonValidation)
		option.pack_start(boutonValidation, False, False, 4)
		option.pack_end(typePartage, False, False, 6)
		vBox.pack_start(option, False, False, 4)
		
		boutonQuitter = gtk.Button("Quitter", stock = gtk.STOCK_QUIT)
		boutonQuitter.connect("clicked", self.quitter, boutonValidation, typePartage, window)
		vBox.pack_end(boutonQuitter, False, False, 2)
		
		window.add(vBox)
		window.show_all()
		gtk.main()
		
if __name__ == '__main__':
	Main()
	
	
	
	
	
	
