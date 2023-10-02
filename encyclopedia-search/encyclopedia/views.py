from django.shortcuts import render, redirect
from django.urls import reverse
from django.http import HttpResponseRedirect
from random import choice
import markdown2

from . import util


def index(request):
    if request.method == "POST":
        substrings = []
        for entry in util.list_entries():
            lower = entry.lower()
            if request.POST.get('q').lower() == lower:
                s = f"wiki/{request.POST.get('q')}"
                return redirect(s)

            elif lower.find(request.POST.get('q').lower()) != -1:
                substrings.append(entry)
        
        if len(substrings) == 0:
            return render(request, "encyclopedia/error.html", {
                "error": f"{request.POST.get('q')} not found!"
            })
            
        else:
            return render(request, "encyclopedia/list.html", {
                "substrings": substrings
            })
            
        
    else:
        return render(request, "encyclopedia/index.html", {
            "entries": util.list_entries()
        })
    

def entry(request, title):
    if request.method == "POST":
        if 'edit' in request.POST:
            s = f"/edit/{title}"
            return redirect(s)

        else:
            substrings = []
            for entry in util.list_entries():
                lower = entry.lower()
                if request.POST.get('q').lower() == lower:
                    return HttpResponseRedirect(f"/wiki/{entry}")

                elif lower.find(request.POST.get('q').lower()) != -1:
                    substrings.append(entry)
            
            if len(substrings) == 0:
                return render(request, "encyclopedia/error.html", {
                    "error": f"{request.POST.get('q')} not found!"
                })

                
            else:
                return render(request, "encyclopedia/list.html", {
                    "substrings": substrings
                })
    
    else:
        entries = util.list_entries()
        if title.lower() in [entry.lower() for entry in entries]:
            return render(request, "encyclopedia/entry.html", {
                "content": markdown2.markdown(util.get_entry(title)), "title": title
            })

        else:
            return render(request, "encyclopedia/error.html", {
                "error": f"{title} not found!"
            })

def new_entry(request):
    if request.method == "POST":
        if request.POST.get('title'):
            if request.POST.get('title').lower() in [entry.lower() for entry in util.list_entries()]:
                return render(request, "encyclopedia/error.html", {
                    "error": f"{request.POST.get('title')} already exists!"
                })

            else:
                util.save_entry(request.POST.get('title'), request.POST.get('content'))
                s = f"wiki/{request.POST.get('title')}"
                return redirect(s)

        else:
            substrings = []
            for entry in util.list_entries():
                lower = entry.lower()
                if request.POST.get('q').lower() == lower:
                    s = f"wiki/{entry}"
                    return redirect(s)

                elif lower.find(request.POST.get('q').lower()) != -1:
                    substrings.append(entry)
            
            if len(substrings) == 0:
                return render(request, "encyclopedia/error.html", {
                    "error": f"{request.POST.get('q')} not found!"
                })

                
            else:
                return render(request, "encyclopedia/list.html", {
                    "substrings": substrings
                })

    else:
        return render(request, "encyclopedia/new_entry.html")

def edit(request, title):
    if request.method == "GET":
        return render(request, "encyclopedia/edit.html", {
            "title": title, "content": util.get_entry(title)
        })

    if request.method == "POST":
        if 'edit' in request.POST:
            util.save_entry(title, request.POST.get('content'))
            return HttpResponseRedirect(f"/wiki/{title}")

        else:
            substrings = []
            for entry in util.list_entries():
                lower = entry.lower()
                if request.POST.get('q').lower() == lower:
                    s = f"wiki/{entry}"
                    return redirect(s)

                elif lower.find(request.POST.get('q').lower()) != -1:
                    substrings.append(entry)
            
            if len(substrings) == 0:
                return render(request, "encyclopedia/error.html", {
                    "error": f"{request.POST.get('q')} not found!"
                })

                
            else:
                return render(request, "encyclopedia/list.html", {
                    "substrings": substrings
                })

def random(request):
    if request.method == "GET":
        entries = util.list_entries()
        entry = choice(entries)
        return redirect(f"wiki/{entry}")
