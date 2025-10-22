# main/views.py
from django.views.generic import TemplateView

def show_main(request):
    return render(request, "index.html")
