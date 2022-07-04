import email
import imp
from pickletools import read_uint1
from pydoc_data.topics import topics
from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.contrib.auth import authenticate, login, logout 
# from django.contrib.auth.forms import UserCreationForm





# Create your views here.
from django.http import HttpResponse
from django.db.models import Q
from .models import Room, Topic, Message, User
from .forms import RoomForm, UserForm, MyUserCreationForm


# rooms = [
#     {'id':1, 'name':'Lets learn python!'},
#     {'id':2, 'name':'Desing with me!'},
#     {'id':3, 'name':'Frontend developers'},

# ]


def loginPage(request):

    page = 'login'

    if request.user.is_authenticated:
        return redirect('home')

    if request.method == 'POST':
        email = request.POST.get('email').lower()
        password = request.POST.get('password')

        try:
            user = User.objects.get(email=email)
        except:
            messages.error(request, 'User does not exist')
        
        user = authenticate(request, email=email, password=password)

        if user is not None:
            login(request, user=user)
            return redirect('home')
        else:
            messages.error(request, 'Username or password does not exist')



    context = {'page':page}
    return render(request, 'base\login_register.html', context) 




def logoutUser(request):
    logout(request)
    return redirect('home')


def registerPage(request):
    form = MyUserCreationForm()
    page = 'register'

    context = {'form':form}


    if request.method == 'POST':
        form = MyUserCreationForm(request.POST)
        if form.is_valid():
            #in order to access the user we need to 'freeze' it hence the commit = false
            user = form.save(commit=False)
            user.username = user.username.lower()
            user.save()
            login(request, user)
            return redirect('home')
        else:
            messages.error(request, 'An error ocurred during registration')

    return render(request, 'base/login_register.html', context)



def home(request):



    q = request.GET.get('q') if request.GET.get('q') !=None else ''

    #Q look up method 
    rooms = Room.objects.filter( Q(topic__name__icontains=q) |
    Q(name__icontains=q)|
    Q(description__icontains=q)
    )

    topics = Topic.objects.all()[0:5]

    room_count = rooms.count()

    room_messages = Message.objects.filter(Q(room__topic__name__icontains=q))

    context = {'rooms':rooms, 'topics':topics, 'room_count':room_count, 'room_messages':room_messages}
    return render(request, 'base/home.html', context)



def room(request, pk):

    room = Room.objects.get(id=pk)
    #This is how you query children from other models in this case is from the Message table 
    #in this case the messages from this room
    room_messages = room.message_set.all().order_by('-created')

    participants = room.participants.all()

    # for i in rooms:
    #     if i['id'] == int(pk):
    #         room= i

    if request.method == 'POST':
        
        message = Message.objects.create(
            user=request.user,
            room = room,
            body = request.POST.get('body')
        )

        #if a new user commented it must be added to the room
        room.participants.add(request.user)
        return redirect('room', pk=room.id)
    
    context = {'room':room, 'room_messages':room_messages, 'participants':participants}
    return render(request, 'base/room.html', context)




def userProfile(request, pk):
    user = User.objects.get(id=pk)
    room_messages = user.message_set.all()
    topics = Topic.objects.all()

    #this is how you get all the children from a specific object 
    rooms = user.room_set.all()
    context = {'user':user, 'rooms':rooms, 'room_messages':room_messages, 'topics':topics}
    return render(request, 'base/profile.html', context)


#decorator to restrinct anons to access this page

@login_required(login_url='login')
def createRoom(request):
    form = RoomForm()
    topics = Topic.objects.all()

    if request.method == 'POST':
        # print(request.POST)
        topic_name = request.POST.get('topic')
        topic, created = Topic.objects.get_or_create(name=topic_name)
        Room.objects.create(
            host = request.user, 
            topic=topic,
            name= request.POST.get('name'),
            description = request.POST.get('description')
        )
        # form = RoomForm(request.POST)

        # if form.is_valid():
        #     room = form.save(commit=False)
        #     room.host = request.user
        #     room.save()
        return redirect('home')

    context = {'form':form, 'topics':topics}
    return render(request, 'base/room_form.html', context)



def updateRoom(request, pk):


    room = Room.objects.get(id=pk)
    #instance prefilled form
    form = RoomForm(instance=room)
    topics = Topic.objects.all()


    if request.user != room.host:
        return HttpResponse('You are not allowed here')


    if request.method == 'POST':
        #we need to tell which room to update, instance**
        topic_name = request.POST.get('topic')
        topic, created = Topic.objects.get_or_create(name=topic_name)
        # form = RoomForm(request.POST, instance=room)
        room.name = request.POST.get('name')
        room.topic = topic
        room.description = request.POST.get('description')
        room.save()

        # if form.is_valid():
        #     form.save()
        return redirect('home')


    context = {'form':form, 'topics':topics, 'room':room}



    return render(request, 'base/room_form.html', context)


def deleteRoom(request, pk):
    room = Room.objects.get(id=pk)
    # form = RoomForm(instance=room)

    if request.user != room.host:
        return HttpResponse('You are not allowed here')

    if request.method == 'POST':
        room.delete()
        return redirect('home')


    return render(request, 'base/delete.html', {"obj":room})

    
def deleteMessage(request, pk):
    message = Message.objects.get(id=pk)
    # form = RoomForm(instance=room)

    if request.user != message.user:
        return HttpResponse('You are not allowed here')

    if request.method == 'POST':
        message.delete()
        return redirect('home')


    return render(request, 'base/delete.html', {"obj":message})



@login_required(login_url=login)
def updateUser(request):
    user = request.user
    form = UserForm(instance=user)


    if request.method == 'POST':
        form = UserForm(request.POST, request.FILES, instance=user)
        if form.is_valid():
            form.save()
            return redirect('user-profile', pk=user.id)

    context = {
        'form': form,
        'user':user
    }

    return render(request, 'base/update-user.html', context=context)


def topicsPage(request):

    q = request.GET.get('q') if request.GET.get('q') !=None else ''


    topics = Topic.objects.filter(name__icontains=q)

    context = {'topics':topics}

    return render(request, 'base/topics.html', context)



def activitiesPage(request):
    room_messages = Message.objects.all()
    context = {'room_messages': room_messages}
    return render(request, 'base/activity.html', context=context)
