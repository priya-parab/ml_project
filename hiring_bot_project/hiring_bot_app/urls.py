from django.urls import path

from hiring_bot_app.views.front_end.views import *
from hiring_bot_app.views.back_end.views import *

urlpatterns = [
    path('', base_page, name='base_page'),
    path('user/login', login_page, name='login_page'),
    path('user/logout', logout_view, name='logout_view'),
    path('Question_set', Question_set, name='Question_set'),
    path('signup', signup, name='signup'),
    path('recruiter_upload_page', recruiter_upload_page, name='recruiter_upload_page'),
    path('convert_to_qqp', convert_to_qqp, name='convert_to_qqp'),
    path('prediction', prediction, name='prediction'),

    path('admin/login_page', admin_login_page, name='admin_login_page'),
    path('admin/login', admin_login, name='admin_login'),
    path('admin/logout', admin_logout, name='admin_logout'),
    path('admin/dashboard', admin, name='admin'),
    path('admin/banners/list/', BannersList.as_view(), name='banners_list'),
    path('admin/banners/create', BannersCreate.as_view(), name='banners_create'),
    path('admin/banners/update/<int:pk>', BannersUpdate.as_view(), name='banners_edit'),
    path('admin/banners/delete/<int:pk>', BannersDelete.as_view(), name='banners_delete'),
    path('admin/user/list/', CustomUserList.as_view(), name='user_list'),
    path('admin/user/create', CustomUserCreate, name='user_create'),
    path('admin/user/update/<int:pk>', CustomUserUpdate.as_view(), name='user_edit'),
    path('admin/user/delete/<int:pk>', CustomUserDelete.as_view(), name='user_delete'),

    path('admin/recruiter/train_page', train_page, name='train_page'),
    path('admin/recruiter/train', train, name='train'),
]
