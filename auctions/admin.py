from django.contrib import admin
from .models import Listing, Bid, Comment, Category

# Register your models here.
class ListingAdmin(admin.ModelAdmin):
    list_display = ('title', 'creator', 'current_price', 'active')

class BidAdmin(admin.ModelAdmin):
    list_display = ('listing', 'bidder', 'amount', 'created_at')

class CommentAdmin(admin.ModelAdmin):
    list_display = ('listing', 'author', 'created_at')

admin.site.register(Category)
admin.site.register(Listing, ListingAdmin)
admin.site.register(Bid, BidAdmin)
admin.site.register(Comment, CommentAdmin)
