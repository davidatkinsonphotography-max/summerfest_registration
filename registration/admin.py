from django.contrib import admin
from django.utils.html import format_html
from .models import ParentProfile, Child, Attendance, TeacherProfile, TeacherClassAssignment, Pass


@admin.register(ParentProfile)
class ParentProfileAdmin(admin.ModelAdmin):
    list_display = ['first_name', 'last_name', 'email', 'phone_number', 'city', 'created_at']
    list_filter = ['how_heard_about', 'attends_church_regularly', 'created_at']
    search_fields = ['first_name', 'last_name', 'email', 'phone_number']
    readonly_fields = ['created_at', 'updated_at']
    
    fieldsets = (
        ('User Account', {
            'fields': ('user',)
        }),
        ('Basic Information', {
            'fields': ('first_name', 'last_name', 'street_address', 'city', 'postcode', 'email', 'phone_number')
        }),
        ('Program Information', {
            'fields': ('how_heard_about', 'additional_information', 'attends_church_regularly', 'which_church')
        }),
        ('Emergency Contact', {
            'fields': ('emergency_contact_name', 'emergency_contact_phone', 'emergency_contact_relationship')
        }),
        ('Consent', {
            'fields': ('first_aid_consent', 'injury_waiver')
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        })
    )


@admin.register(Child)
class ChildAdmin(admin.ModelAdmin):
    list_display = ['first_name', 'last_name', 'parent_name', 'child_class', 'date_of_birth', 'qr_code_display']
    list_filter = ['child_class', 'gender', 'has_dietary_needs', 'has_medical_needs', 'photo_consent']
    search_fields = ['first_name', 'last_name', 'parent__first_name', 'parent__last_name']
    readonly_fields = ['qr_code_id', 'qr_code_display', 'created_at', 'updated_at']
    
    def parent_name(self, obj):
        return f"{obj.parent.first_name} {obj.parent.last_name}"
    parent_name.short_description = 'Parent'
    
    def qr_code_display(self, obj):
        if obj.qr_code_image:
            return format_html('<img src="{}" width="50" height="50" />', obj.qr_code_image.url)
        return "No QR Code"
    qr_code_display.short_description = 'QR Code'
    
    fieldsets = (
        ('Parent', {
            'fields': ('parent',)
        }),
        ('Basic Information', {
            'fields': ('first_name', 'last_name', 'date_of_birth', 'gender', 'child_class')
        }),
        ('Health Information', {
            'fields': ('has_dietary_needs', 'dietary_needs_detail', 'has_medical_needs', 'medical_allergy_details')
        }),
        ('Consent', {
            'fields': ('photo_consent',)
        }),
        ('QR Code', {
            'fields': ('qr_code_id', 'qr_code_display'),
            'classes': ('collapse',)
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        })
    )


@admin.register(Attendance)
class AttendanceAdmin(admin.ModelAdmin):
    list_display = ['child_name', 'child_class', 'date', 'time_in', 'time_out', 'checked_in_by', 'checked_out_by']
    list_filter = ['date', 'child__child_class']
    search_fields = ['child__first_name', 'child__last_name']
    readonly_fields = ['date']
    
    def child_name(self, obj):
        return f"{obj.child.first_name} {obj.child.last_name}"
    child_name.short_description = 'Child'
    
    def child_class(self, obj):
        return obj.child.get_child_class_display()
    child_class.short_description = 'Class'


class TeacherClassAssignmentInline(admin.TabularInline):
    model = TeacherClassAssignment
    extra = 1
    

@admin.register(TeacherProfile)
class TeacherProfileAdmin(admin.ModelAdmin):
    list_display = ['teacher_name', 'get_assigned_classes_display']
    inlines = [TeacherClassAssignmentInline]
    
    def teacher_name(self, obj):
        return obj.user.get_full_name() or obj.user.username
    teacher_name.short_description = 'Teacher Name'
    
    def get_assigned_classes_display(self, obj):
        classes = obj.get_assigned_class_names()
        if classes:
            return ', '.join(classes)
        return 'No classes assigned'
    get_assigned_classes_display.short_description = 'Assigned Classes'


@admin.register(TeacherClassAssignment)
class TeacherClassAssignmentAdmin(admin.ModelAdmin):
    list_display = ['teacher_name', 'class_code', 'get_class_display', 'is_primary']
    list_filter = ['class_code', 'is_primary']
    search_fields = ['teacher__user__first_name', 'teacher__user__last_name', 'teacher__user__username']
    
    def teacher_name(self, obj):
        return obj.teacher.user.get_full_name() or obj.teacher.user.username
    teacher_name.short_description = 'Teacher'
    
    def get_class_display(self, obj):
        return obj.get_class_code_display()
    get_class_display.short_description = 'Class Name'


@admin.register(Pass)
class PassAdmin(admin.ModelAdmin):
    list_display = ['parent_name', 'type', 'valid_from', 'valid_to', 'amount_paid', 'is_currently_valid', 'purchased_at']
    list_filter = ['type', 'valid_from', 'valid_to']
    search_fields = ['parent__first_name', 'parent__last_name', 'parent__user__username']
    date_hierarchy = 'purchased_at'
    readonly_fields = ['purchased_at', 'created_at', 'updated_at']
    
    fieldsets = (
        ('Pass Details', {
            'fields': ('parent', 'type', 'valid_from', 'valid_to', 'amount_paid')
        }),
        ('Stripe Integration', {
            'fields': ('stripe_payment_id', 'stripe_session_id'),
            'classes': ('collapse',)
        }),
        ('Timestamps', {
            'fields': ('purchased_at', 'created_at', 'updated_at'),
            'classes': ('collapse',)
        })
    )
    
    def parent_name(self, obj):
        return f"{obj.parent.first_name} {obj.parent.last_name}"
    parent_name.short_description = 'Parent'
    parent_name.admin_order_field = 'parent__first_name'
    
    def is_currently_valid(self, obj):
        from datetime import date
        is_valid = obj.is_valid_for_date(date.today())
        if is_valid:
            return format_html('<span style="color: green;">✓ Valid</span>')
        else:
            return format_html('<span style="color: red;">✗ Expired</span>')
    is_currently_valid.short_description = 'Currently Valid'
    is_currently_valid.admin_order_field = 'valid_to'


# Customize admin site header
admin.site.site_header = "Summerfest Registration Admin"
admin.site.site_title = "Summerfest Admin"
admin.site.index_title = "Welcome to Summerfest Administration"
