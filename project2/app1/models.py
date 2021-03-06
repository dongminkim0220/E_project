
#from __futre__ import unicode_literals

from django.db import models

# Create your models here.

class Image(models.Model):
	image_name = models.CharField(max_length=200)
	pub_date = models.DateTimeField('date published')
	image = models.ImageField(upload_to='images/', default='static/RPi.jpeg')
	
	def __str__(self):
		
		return self.image_name

