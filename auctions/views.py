from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
from django.db import IntegrityError
from django.http import HttpResponse, HttpResponseRedirect
from django.shortcuts import render, redirect
from django.urls import reverse

from .models import User, Listing, Bid, Comment, Category
from .forms import ListingForm, BidForm, CommentForm


def index(request):
    return render(request, "auctions/index.html", {
        "listings": Listing.objects.filter(active=True)
    })


def login_view(request):
    if request.method == "POST":

        # Attempt to sign user in
        username = request.POST["username"]
        password = request.POST["password"]
        user = authenticate(request, username=username, password=password)

        # Check if authentication successful
        if user is not None:
            login(request, user)
            return HttpResponseRedirect(reverse("index"))
        else:
            return render(request, "auctions/login.html", {
                "message": "Invalid username and/or password."
            })
    else:
        return render(request, "auctions/login.html")


def logout_view(request):
    logout(request)
    return HttpResponseRedirect(reverse("index"))


def register(request):
    if request.method == "POST":
        username = request.POST["username"]
        email = request.POST["email"]

        # Ensure password matches confirmation
        password = request.POST["password"]
        confirmation = request.POST["confirmation"]
        if password != confirmation:
            return render(request, "auctions/register.html", {
                "message": "Passwords must match."
            })

        # Attempt to create new user
        try:
            user = User.objects.create_user(username, email, password)
            user.save()
        except IntegrityError:
            return render(request, "auctions/register.html", {
                "message": "Username already taken."
            })
        login(request, user)
        return HttpResponseRedirect(reverse("index"))
    else:
        return render(request, "auctions/register.html")


@login_required
def create_listing(request):
    if request.method == "POST":
        form = ListingForm(request.POST)
        if form.is_valid():
            listing = form.save(commit=False)
            listing.creator = request.user
            listing.current_price = form.cleaned_data['starting_bid']
            listing.save()
            return redirect("listing", listing_id=listing.id) 

    else:
        form = ListingForm()
    return render(request, "auctions/create_listing.html", {
        "form": form,
    })

def listing(request, listing_id):
    listing = Listing.objects.get(pk=listing_id)
    in_watchlist = request.user in listing.watchers.all() if request.user.is_authenticated else False
    return render(request, "auctions/listing.html", {
        "listing": listing,
        "in_watchlist": in_watchlist,
        "bid_form": BidForm(),
        "comment_form": CommentForm(),
        "comments": listing.comments.all().order_by('-created_at')
    })

@login_required
def watchlist(request):
    return render(request, "auctions/watchlist.html", {
        "listings": request.user.watchlist.all()
    })

@login_required
def watchlist_add(request, listing_id):
    listing = Listing.objects.get(pk=listing_id)
    request.user.watchlist.add(listing)
    return redirect("listing", listing_id=listing_id)

@login_required
def watchlist_remove(request, listing_id):
    listing = Listing.objects.get(pk=listing_id)
    request.user.watchlist.remove(listing)
    return redirect("listing", listing_id=listing_id)