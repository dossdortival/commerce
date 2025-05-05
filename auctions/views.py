from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
from django.db import IntegrityError
from django.http import HttpResponseRedirect
from django.shortcuts import render, redirect
from django.urls import reverse
from django.contrib import messages

from .models import User, Listing, Bid, Category
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


@login_required
def bid(request, listing_id):
    listing = Listing.objects.get(pk=listing_id)
    if request.method == "POST":
        form = BidForm(request.POST)
        if form.is_valid():
            amount = form.cleaned_data['amount']
            if amount >= listing.starting_bid and (not listing.bids.exists() or amount > listing.current_price):
                bid = Bid(amount=amount, bidder=request.user, listing=listing)
                bid.save()
                listing.current_price = amount
                listing.save()
                messages.success(request, "Bid placed successfully!")
            else:
                messages.error(request, "Bid must be at least as large as starting bid and greater than any other bids.")
    return redirect("listing", listing_id=listing_id)


@login_required
def close(request, listing_id):
    listing = Listing.objects.get(pk=listing_id)
    if request.user == listing.creator:
        if listing.bids.exists():
            highest_bid = listing.bids.first()
            listing.winner = highest_bid.bidder
        listing.active = False
        listing.save()
        messages.success(request, "Auction closed successfully!")
    return redirect("listing", listing_id=listing_id)

@login_required
def comment(request, listing_id):
    listing = Listing.objects.get(pk=listing_id)
    if request.method == "POST":
        form = CommentForm(request.POST)
        if form.is_valid():
            comment = form.save(commit=False)
            comment.author = request.user
            comment.listing = listing
            comment.save()
    return redirect("listing", listing_id=listing_id)


def categories(request):
    return render(request, "auctions/categories.html", {
        "categories": Category.objects.all()
    })


def category(request, category_id):
    category = Category.objects.get(pk=category_id)
    return render(request, "auctions/category.html", {
        "category": category,
        "listings": category.listing_set.filter(active=True)
    })