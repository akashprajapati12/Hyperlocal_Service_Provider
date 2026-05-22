from django.contrib import admin
from .models import Review


@admin.register(Review)
class ReviewAdmin(admin.ModelAdmin):
    list_display = ('user', 'service', 'rating', 'review_date')
    list_filter = ('rating',)
    search_fields = ('user__username', 'service__service_name', 'comment')
