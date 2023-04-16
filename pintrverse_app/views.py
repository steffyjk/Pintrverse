import datetime
import json
from functools import reduce
from operator import or_

from django.http import HttpResponse
from django.shortcuts import redirect, render
from django.urls import reverse_lazy, reverse
from django.views import generic
from django.contrib import messages
from rest_framework.response import Response

from pintrverse_app.filters import UserFilterSet, PinFilterSet
from pintrverse_app.forms import CreatePinForm, CategoryForm, TagForm
from pintrverse_app.models import Pin, SavedPin, Tag, Like, Category
# from pintrverse_app.utils import extract_keywords, get_history_list
# from pintrverse_app.utils import extract_keywords, get_history_list
from users.models import User
from django.db.models import Q
from pathlib import Path
import getpass
import sqlite3
from pprint import pprint
from django.db.models import Case, When, Value, IntegerField, BooleanField, F
from django.db.models.functions import Coalesce
import os
import shutil
from functools import reduce
from operator import or_
from django.db.models import Case, When, Value, CharField
from django.db.models.functions import Lower


# Retrieve the login name of the current user
def get_current_user():
    user = os.getlogin()
    print("Current logged-in user:", user)
    return user


def detect_os(request):
    logged_user = get_current_user()
    user_agent = request.META.get('HTTP_USER_AGENT', '').lower()

    if 'windows' in user_agent:
        path_to_check = Path(r'C:\Users\%s\AppData\Local\Google\Chrome\User Data\Default\History' % (logged_user))
        print(path_to_check)
        # Check if the path exists
        if path_to_check.is_file():
            shutil.copy(path_to_check, r'C:\Users\%s\Desktop\History' % (logged_user))
            conn = sqlite3.connect(r'C:\Users\%s\Desktop\History' % (logged_user))
            cursor = conn.cursor()

            # Retrieve search history from the 'keyword_search_terms' table
            cursor.execute("SELECT * FROM keyword_search_terms")
            rows = cursor.fetchall()
            pprint(rows)

            # Close the database connection
            # j
            # FETCH KEYWORD FROM ROWS FETCHED
            history_keywords = []
            for row in rows:
                if row[2] not in history_keywords:
                    history_keywords.append(row[2])

            # Close the database connection
            # cursor.close()
            # conn.close()
            print(f"Chrome Installed.")
        else:
            history_keywords = []
            print(f"Chrome is not installed.")

        # return 'linux'
        return history_keywords
    elif 'mac' in user_agent:
        pass
        path_to_check = Path(f'/Users/{logged_user}/Library/Application Support/Google/Chrome/Default/History')

        # # Check if the path exists
        if path_to_check.is_file():
            shutil.copy(path_to_check, r'/Users/%s/Desktop' % (logged_user))
            conn = sqlite3.connect(r'/Users/%s/Desktop' % (logged_user))
            cursor = conn.cursor()
            # Retrieve search history from the 'keyword_search_terms' table
            cursor.execute("SELECT * FROM keyword_search_terms")
            rows = cursor.fetchall()
            pprint(rows)
            # # Close the database connection
            # cursor.close()
            # conn.close()
            # FETCH KEYWORD FROM ROWS FETCHED
            history_keywords = []
            for row in rows:
                history_keywords.append(row[2])

            # # Close the database connection
            # cursor.close()
            # conn.close()
            print(f"Chrome Installed.")
        else:
            history_keywords = []
            print(f"Chrome is not installed.")

            # return 'linux'
            return history_keywords
    elif 'linux' in user_agent:

        path_to_check = Path(f'/home/{logged_user}/.config/google-chrome/Default/History')

        # # Check if the path exists
        if path_to_check.is_file():
            shutil.copy(path_to_check, r'/home/%s/Desktop/History' % (logged_user))
            conn = sqlite3.connect(r'/home/%s/Desktop/History' % (logged_user))
            cursor = conn.cursor()

            #     # Retrieve search history from the 'keyword_search_terms' table
            cursor.execute("SELECT * FROM keyword_search_terms")
            rows = cursor.fetchall()
            pprint(rows)

            # Close the database connection
            # j
            # FETCH KEYWORD FROM ROWS FETCHED
            history_keywords = []
            for row in rows:
                if row[2] not in history_keywords:
                    history_keywords.append(row[2])

            # Close the database connection
            # cursor.close()
            # conn.close()
            print(f"Chrome Installed.")
        else:
            history_keywords = []
            print(f"Chrome is not installed.")

        return history_keywords
    else:
        # Unable to detect OS
        return 'Error'


# Create your views here.
class ListAllPins(generic.ListView):
    model = Pin
    template_name = 'pintrverse_app/pin_list.html'
    context_object_name = 'object_list'
    def get_queryset(self):
        queryset = super().get_queryset()

        # Check if the "my_param" parameter is in the request
        search = self.request.GET.get('search')
        if search:
            queryset = queryset.filter(
                Q(title__icontains=search) |
                Q(about__icontains=search) |
                Q(tag__name__icontains=search)
            )

        return queryset

    def get_context_data(self, **kwargs):
        context = super(ListAllPins, self).get_context_data(**kwargs)
        for j in context:
            print(j)
        pins = Pin.objects.all()
        print("---")
        print(self.request.session)
        # keywords = sorted(keywords,reverse=True)

        if 'keywords' in self.request.session:
            keywords = self.request.session['keywords']
            if keywords != None:
                try:
                    filter_expr = reduce(or_, [Q(tag__name__icontains=value) for value in keywords])
                    # filter_expr = (tag__name__icontains=value)
                    # # Filter queryset of YourModel based on related field value
                    mldata = Pin.objects.filter(filter_expr)
                    mldata = mldata.reverse()
                    context['mldata'] = mldata
                    print(mldata)
                except:
                    pass
        else:
            context['mldata'] = []

        if self.request.user.is_authenticated:
            pins_saved = []
            pins_liked = []
            for pin in pins:
                try:
                    saved = SavedPin.objects.get(user=self.request.user, pin=pin)
                    pins_saved.append(saved.pin.id)
                except SavedPin.DoesNotExist:
                    pass
                try:
                    liked = Like.objects.get(user=self.request.user, pin=pin)
                    pins_liked.append(liked.pin.id)
                except Like.DoesNotExist:
                    pass
            context['saved_pins'] = pins_saved
            context['liked_pins'] = pins_liked
        return context


class CreatePinView(generic.CreateView):
    model = Pin
    template_name = 'pintrverse_app/create_pin.html'
    form_class = CreatePinForm
    success_url = reverse_lazy("home")

    def get_context_data(self, **kwargs):
        context = super(CreatePinView, self).get_context_data(**kwargs)
        context['category'] = CategoryForm()
        context['tag'] = TagForm()
        return context

    def form_valid(self, form):
        form.instance.user = self.request.user
        messages.success(self.request, 'Your new pin created.')
        return super(CreatePinView, self).form_valid(form)

    def post(self, request, *args, **kwargs):
        if 'categorybtn' in request.POST:
            catform = CategoryForm(request.POST)
            if catform.is_valid():
                catform.save()
            else:
                messages.error(request, "Something Went Wrong Creating Category !")

        if 'tagbtn' in request.POST:
            tagform = TagForm(request.POST)
            if tagform.is_valid():
                tagform.save()
            else:
                messages.error(request, "Something Went Wrong Creating Tag !")
        return super().post(request, *args, **kwargs)


class TodayPinView(generic.ListView):
    model = Pin
    template_name = 'pintrverse_app/todays_pin.html'
    context_object_name = 'object_list'
    queryset = Pin.objects.filter(created_at__date=datetime.date.today())

    def get_queryset(self):
        queryset = super().get_queryset()

        # Check if the "my_param" parameter is in the request
        today_search = self.request.GET.get('today_search')
        if today_search:
            queryset = queryset.filter(
                Q(title__icontains=today_search) |
                Q(about__icontains=today_search) |
                Q(tag__name__icontains=today_search)
            )

        return queryset

    def get_context_data(self, **kwargs):
        context = super(TodayPinView, self).get_context_data(**kwargs)
        for j in context:
            print(j)
        pins = Pin.objects.all()
        if self.request.user.is_authenticated:
            pins_saved = []
            pins_liked = []
            for pin in pins:
                try:
                    saved = SavedPin.objects.get(user=self.request.user, pin=pin)
                    pins_saved.append(saved.pin.id)
                except SavedPin.DoesNotExist:
                    pass
                try:
                    liked = Like.objects.get(user=self.request.user, pin=pin)
                    pins_liked.append(liked.pin.id)
                except Like.DoesNotExist:
                    pass
            context['saved_pins'] = pins_saved
            context['liked_pins'] = pins_liked
        return context


class ParticularPinDetail(generic.DetailView):
    model = Pin
    template_name = 'pintrverse_app/particular_pin.html'
    slug_url_kwarg = 'pin_id'
    slug_field = 'id'

    # def get_context_data(self, **kwargs):
    #     context = super(ParticularPinDetail,self).get_context_data(**kwargs)
    #     print(context['pin'].tag)


class SavePinView(generic.View):

    def post(self, request, *args, **kwargs):
        if SavedPin.objects.filter(pin__id=kwargs['pk'], user=self.request.user).exists():
            messages.warning(self.request, 'Already saved')
            return redirect(to='home')
        else:
            pin_id = kwargs['pk']
            try:
                save_p = SavedPin.objects.create(user_id=request.user.id,
                                                 pin_id=pin_id)
                messages.success(self.request, 'Saved successfully')
            except Exception as e:
                messages.error(self.request, f"{e}")
                return redirect(to='home')
            return redirect(to='home')


class UnSavePinView(generic.View):

    def post(self, request, *args, **kwargs):
        try:
            saved_pin = SavedPin.objects.get(pin__id=kwargs['pk'], user=self.request.user)
            saved_pin.delete()
            messages.success(self.request, 'Unsaved Pin')
        except SavedPin.DoesNotExist:
            messages.error(self.request, "Pin Not Saved Please Save It First !")
        return redirect(to='home')


class LikeView(generic.View):

    def post(self, request, *args, **kwargs):
        if Like.objects.filter(pin__id=kwargs['pk'], user=self.request.user).exists():
            messages.warning(self.request, 'Already Liked')
            return redirect(to='home')
        else:
            pin_id = kwargs['pk']
            try:
                save_p = Like.objects.create(user_id=request.user.id,
                                             pin_id=pin_id)
                messages.success(self.request, 'Liked successfully')
            except Exception as e:
                messages.error(self.request, f"{e}")
                return redirect(to='home')
            return redirect(to='home')


class UnlikeView(generic.View):

    def post(self, request, *args, **kwargs):
        try:
            saved_pin = Like.objects.get(pin__id=kwargs['pk'], user=self.request.user)
            saved_pin.delete()
            messages.success(self.request, 'Unliked Pin')
        except Like.DoesNotExist:
            messages.error(self.request, "Pin Not Liked Please Save It First !")
        return redirect(to='home')


from rest_framework.generics import GenericAPIView


class RestApiForSave(GenericAPIView):

    def get(self, request, *args, **kwargs):
        req = self.request
        post_id = req.GET.get('post_id')
        user_id = req.GET.get('user_id')
        if SavedPin.objects.filter(pin__id=post_id, user=user_id).exists():
            return Response({'status': 'exists'})
        else:
            return Response({'status': 'not_exists'})


class ShowAllSavedPin(generic.ListView):
    model = SavedPin
    template_name = 'pintrverse_app/show_all_saved_pins.html'

    def get_queryset(self):
        queryset = super().get_queryset()
        # Add custom filtering or ordering to the queryset
        queryset = queryset.filter(user_id=self.request.user.id)
        return queryset


#
# # # FUNCTIONAL BASED FETCH PIN FROM USER's history's keyword
# def fetch_keyword_pin(request):
#     keywords = extract_keywords(get_history_list(5))
#     for keyword in keywords:
#         fetched_tag = Tag.objects.filter(name=str(keyword))
#         break
#     fetched_pin = Pin.objects.filter(tag__id__in=fetched_tag.all())
#     return HttpResponse(fetched_pin)


# class FetchKeyWordPin(generic.ListView):
#     model = Pin
#     template_name = 'pintrverse_app/fetched_pin.html'
#     keywords = extract_keywords(get_history_list(10))  # function for fetch history & filter keywords from that
#     # print("---------key", keywords)
#     ls = []
#     for keyword in keywords:
#         if fetched_tag := Tag.objects.filter(name=str(keyword)):  # find TAGS Based on keyword [ history ]
#             for i in fetched_tag.all():
#                 queryset = Pin.objects.filter(tag=i.id)  # Find Pin based on Tag
#                 ls.append(queryset)
#         queryset = []
#         for j in ls:
#             queryset += j


class LikeUnlikePin(generic.View):
    def get(self, request, pin_id):
        pin_obj = Pin.objects.get(id=pin_id)
        if pin_obj.pin_likes and pin_obj.pin_likes.filter(user=request.user.id).exists():
            pin_obj.pin_likes.delete(request.user)
        else:
            pin_obj.pin_likes.add(request.user)
        return redirect(reverse('detail_pin', kwargs={'id': pin_id}))


def search_users(request):
    users = User.objects.all()
    filter = UserFilterSet(request.GET, queryset=users)
    users = filter.qs
    context = {
        'users': users,
        'filter': filter
    }
    return render(request, 'pintrverse_app/search_users.html', context)


def search_pins(request):
    pins = Pin.objects.all()
    filter = PinFilterSet(request.GET, queryset=pins)
    pins = filter.qs
    context = {
        'pins': pins,
        'filter': filter
    }
    return render(request, 'pintrverse_app/search_pins.html', context)


class UpdatePin(generic.UpdateView):
    model = Pin
    fields = ['pin_file', 'title', 'about', 'alt_text', 'destination_link', 'category', 'tag']
    template_name = 'pintrverse_app/pin_update.html'
    success_url = reverse_lazy('home')


class DeletePinView(generic.DeleteView):
    model = Pin
    template_name = 'pintrverse_app/confirm_pin_delete.html'
    success_url = reverse_lazy('home')


# FETCH OTHER USER OS SYSTEM
from django.http import JsonResponse


def get_user_os(request):
    user_agent = request.META.get('HTTP_USER_AGENT')
    print("---> THIS", request.META.get('LOGNAME'))
    LOG_NAME = request.META.get('LOGNAME')
    if user_agent:
        if 'Windows' in user_agent:
            os_name = 'Windows'
        elif 'Mac' in user_agent:
            os_name = 'Mac'
        elif 'Linux' in user_agent:
            os_name = 'Linux'
        else:
            os_name = 'Unknown'

        response_data = {'os_name': os_name,
                         'LOG_NAME': LOG_NAME}
    else:
        response_data = {'error': 'User-Agent header not found in the request'}

    return JsonResponse(response_data)

import getpass
from django.http import HttpResponse


def os_user_data(request):
    user = getpass.getuser()
    return HttpResponse(f"The current OS user is {user}")

from django.http import JsonResponse

def set_logname(request):
    username = request.POST.get('logname')
    request.META['LOGNAME'] = username
    meta_dict = {}
    for key, value in request.META.items():
        # Skip keys with non-serializable values
        if not isinstance(value, (int, str, float, bool, list, dict)):
            continue
        meta_dict[key] = value
    return JsonResponse({'status': 'success',
                         'REQUEST':json.dumps(meta_dict)})



from rest_framework.decorators import api_view
from rest_framework.response import Response
from django.views.decorators.csrf import csrf_exempt
import re

def iterate_words_excluding_special_characters(string):
    # Split the string into words using space as delimiter
    words = string.split()
    # Define regex pattern to match special characters
    pattern = r'[^a-zA-Z0-9]'
    # Iterate over the words and filter out words containing special characters
    filtered_words = [word for word in words if not re.search(pattern, word)]
    return filtered_words

@csrf_exempt
@api_view(['POST','GET'])
def history_extension_api_view(request):
    try:
        # Check if data is present in the POST request
        if 'data' not in request.data:
            response_data = {'error': 'Data not received'}
            return Response(response_data, status=400)

        # Retrieve the JSON data from the POST request
        data = request.data['data']
        sdata = data[:50]
        keywords = []
        for data in sdata:
            title = data['title']
            pattern = r'\(.*?\)'
            # Use re.sub to replace the matches with an empty string
            result = re.sub(pattern, '', title)
            if result not in keywords:
                words = iterate_words_excluding_special_characters(result)
                for word in words:
                    print(word)
                    if word not in keywords:
                        keywords.append(word)

        request.session['keywords'] = keywords
        # Process the received data as needed (e.g., save to database, perform additional operations, etc.)
        # Example: Print the received data
        # print(data)

        # Return a JSON response indicating success
        response_data = {'message': 'Data received successfully'}
        return Response(response_data, status=200)

    except Exception as e:
        # Return a JSON response with error message for any unhandled exceptions
        response_data = {'error': str(e)}
        return Response(response_data, status=500)
