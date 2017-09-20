from django.shortcuts import render
from imageUploader import models
from django.views.generic.base import TemplateView

# Create your views here.


class Image(TemplateView):
    template_name = "image.html"
    def get(self, request, *args, **kwargs):
        image = models.Image.objects.filter(id=self.kwargs["id"])
        if not len(image):
          return render(request, "404.html", {})
        return super(Image, self).get(request, **kwargs)

    def get_context_data(self, **kwargs):
        context = super(Image, self).get_context_data(**kwargs)
        image = models.Image.objects.filter(id=self.kwargs["id"])
        context["image"] = image
        return context
