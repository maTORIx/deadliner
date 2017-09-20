from django.db import models
import uuid
import os

# Create your models here.
def get_image_path(self, filename):
      """カスタマイズした画像パスを取得する.

      :param self: インスタンス (models.Model)
      :param filename: 元ファイル名
      :return: カスタマイズしたファイル名を含む画像パス
      """
      prefix = 'images/'
      name = str(uuid.uuid4()).replace('-', '')
      extension = os.path.splitext(filename)[-1]
      return prefix + name + extension

class Image(models.Model):
    image = models.ImageField(null=False, upload_to="/images")