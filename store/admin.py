from django.contrib import admin
from .models import Product, Category, ProductImage , Coupon
from .models import Slide

class ProductImageInline(admin.TabularInline):  # or admin.StackedInline if you prefer vertical layout
    model = ProductImage
    extra = 1
class ProductAdmin(admin.ModelAdmin):
    list_display = ('name', 'price', 'image', 'description', 'category')
    search_fields = ('name',)
    list_filter = ('category',)
    filter_horizontal = ('cross_sells',)

    fieldsets = (
        (None, {
            'fields': ('name', 'description', 'price', 'image', 'category', 'stock')
        }),
        ('Product Recommendations', {
            'fields': ('upsell_product', 'cross_sells')
        }),
    )
    inlines = [ProductImageInline]      

admin.site.register(Product, ProductAdmin)
admin.site.register(Category)
admin.site.register(Coupon)
admin.site.register(Slide)