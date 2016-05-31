
"""
This file contains the generic, assorted views that don't fall under one of
the other applications. Views are django's way of processing e.g. html
templates on the fly.

"""
from django.contrib.admin.sites import site
from django.conf import settings
from django.contrib.admin.views.decorators import staff_member_required
from django.shortcuts import render

from evennia import SESSION_HANDLER
from evennia.objects.models import ObjectDB
from evennia.players.models import PlayerDB

from django.contrib.auth import login

_BASE_CHAR_TYPECLASS = settings.BASE_CHARACTER_TYPECLASS


def page_index(request):
    """
    Main root page.
    """

    # handle webclient-website shared login

    csession = request.session
    csessid = request.session.session_key
    player = request.user
    # check if user has authenticated to website
    if player.is_authenticated():
        # Try to login all the player's webclient sessions - only
        # unloggedin ones will actually be logged in.
        print "website: player auth, trying to connect sessions"
        for session in SESSION_HANDLER.sessions_from_csessid(csessid):
            print "session to connect:", session
            if session.protocol_key in ("websocket", "ajax/comet"):
                SESSION_HANDLER.login(session, player)
                session.csessid = csession.session_key
        csession["logged_in"] = player.id
    elif csession.get("logged_in"):
        # The webclient has previously registered a login to this csession
        print "website: csession logged in, trying to login"
        player = PlayerDB.objects.get(id=csession.get("logged_in"))
        login(request, player)
    else:
        csession["logged_in"] = None

    print ("website session:", request.session.session_key, request.user, request.user.is_authenticated())

    # Some misc. configurable stuff.
    # TODO: Move this to either SQL or settings.py based configuration.
    fpage_player_limit = 4

    # A QuerySet of the most recently connected players.
    recent_users = PlayerDB.objects.get_recently_connected_players()[:fpage_player_limit]
    nplyrs_conn_recent = len(recent_users) or "none"
    nplyrs = PlayerDB.objects.num_total_players() or "none"
    nplyrs_reg_recent = len(PlayerDB.objects.get_recently_created_players()) or "none"
    nsess = SESSION_HANDLER.player_count()
    # nsess = len(PlayerDB.objects.get_connected_players()) or "no one"

    nobjs = ObjectDB.objects.all().count()
    nrooms = ObjectDB.objects.filter(db_location__isnull=True).exclude(db_typeclass_path=_BASE_CHAR_TYPECLASS).count()
    nexits = ObjectDB.objects.filter(db_location__isnull=False, db_destination__isnull=False).count()
    nchars = ObjectDB.objects.filter(db_typeclass_path=_BASE_CHAR_TYPECLASS).count()
    nothers = nobjs - nrooms - nchars - nexits

    pagevars = {
        "page_title": "Front Page",
        "players_connected_recent": recent_users,
        "num_players_connected": nsess or "no one",
        "num_players_registered": nplyrs or "no",
        "num_players_connected_recent": nplyrs_conn_recent or "no",
        "num_players_registered_recent": nplyrs_reg_recent or "no one",
        "num_rooms": nrooms or "none",
        "num_exits": nexits or "no",
        "num_objects": nobjs or "none",
        "num_characters": nchars or "no",
        "num_others": nothers or "no"
    }

    return render(request, 'index.html', pagevars)


def to_be_implemented(request):
    """
    A notice letting the user know that this particular feature hasn't been
    implemented yet.
    """

    pagevars = {
        "page_title": "To Be Implemented...",
    }

    return render(request, 'tbi.html', pagevars)


@staff_member_required
def evennia_admin(request):
    """
    Helpful Evennia-specific admin page.
    """
    return render(
        request, 'evennia_admin.html', {
            'playerdb': PlayerDB})


def admin_wrapper(request):
    """
    Wrapper that allows us to properly use the base Django admin site, if needed.
    """
    return staff_member_required(site.index)(request)
