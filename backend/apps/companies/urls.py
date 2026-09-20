from django.urls import path
from .views import CompanyDetailView, CompanyListCreateView, InvitationAcceptView, InvitationCreateView, MemberListView, MemberUpdateView

urlpatterns = [
    path("", CompanyListCreateView.as_view()), path("invitations/accept/", InvitationAcceptView.as_view()),
    path("<uuid:company_id>/", CompanyDetailView.as_view()), path("<uuid:company_id>/members/", MemberListView.as_view()),
    path("<uuid:company_id>/invitations/", InvitationCreateView.as_view()), path("<uuid:company_id>/members/<uuid:membership_id>/", MemberUpdateView.as_view()),
]
