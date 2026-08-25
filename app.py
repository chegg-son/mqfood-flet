import flet as ft

import api
from config import BG_COLOR, PRIMARY
from storage import Storage
from views.catalog_view import build_catalog_view
from views.cart_view import build_cart_view
from views.checkout_view import build_checkout_view
from views.home_view import build_home_view
from views.login_view import build_login_view
from views.orders_view import build_invoice_view, build_order_detail_view, build_orders_view
from views.payment_view import build_payment_view
from views.product_detail_view import build_product_detail_view

# Tab destinations shown in the bottom NavigationBar (index -> route)
TAB_ROUTES = {0: "/", 1: "/catalog", 2: "/cart", 3: "/orders"}
ROUTE_TO_INDEX = {route: index for index, route in TAB_ROUTES.items()}


async def main(page: ft.Page):
    page.title = "MQFood"
    page.theme_mode = ft.ThemeMode.LIGHT
    page.theme = ft.Theme(
        color_scheme_seed=PRIMARY,
        page_transitions=ft.PageTransitionsTheme(
            android=ft.PageTransitionTheme.ZOOM,
            ios=ft.PageTransitionTheme.CUPERTINO,
            linux=ft.PageTransitionTheme.ZOOM,
            macos=ft.PageTransitionTheme.ZOOM,
            windows=ft.PageTransitionTheme.ZOOM,
        ),
    )
    page.bgcolor = BG_COLOR
    page.padding = 0
    page.spacing = 0

    storage = Storage(page)
    await storage.init()

    # Payloads passed between pushed screens (product, order, payment data)
    session = {}

    # Root tab currently shown in the bottom NavigationBar. Pushed screens
    # (product/checkout/payment/invoice) keep this tab underneath them.
    # The root view keeps a constant route ("/") so switching tabs updates it
    # in place without a page transition; only pushed screens animate.
    current_tab = "/"

    # Cache built tab views to avoid rebuilding on every navigation
    view_cache = {}

    def clear_view_cache(*routes):
        if not routes:
            view_cache.clear()
        else:
            for r in routes:
                view_cache.pop(r, None)

    # ── Shared view helpers ────────────────────────────────────────────────
    def _wrap(content, route, nav=None):
        return ft.View(
            route=route,
            controls=[content],
            navigation_bar=nav,
            padding=0,
            spacing=0,
            bgcolor=BG_COLOR,
        )

    def _nav_bar(selected_index):
        return ft.NavigationBar(
            selected_index=selected_index,
            on_change=lambda e: page.navigate(TAB_ROUTES[e.control.selected_index]),
            destinations=[
                ft.NavigationBarDestination(icon=ft.Icons.HOME_OUTLINED, selected_icon=ft.Icons.HOME, label="Beranda"),
                ft.NavigationBarDestination(icon=ft.Icons.STORE_OUTLINED, selected_icon=ft.Icons.STORE, label="Katalog"),
                ft.NavigationBarDestination(icon=ft.Icons.SHOPPING_CART_OUTLINED, selected_icon=ft.Icons.SHOPPING_CART, label="Keranjang"),
                ft.NavigationBarDestination(icon=ft.Icons.RECEIPT_LONG_OUTLINED, selected_icon=ft.Icons.RECEIPT_LONG, label="Pesanan"),
            ],
        )

    # ── Navigation callbacks ───────────────────────────────────────────────
    def open_detail(product):
        session["product"] = product
        page.navigate("/product")

    def open_order_detail(order):
        session["order"] = order
        page.navigate("/order")

    def go_checkout():
        page.navigate("/checkout")

    def go_payment_from_checkout(body):
        session["order"] = body.get("order", {})
        session["payment"] = body.get("payment")
        session["payment_back_route"] = "/orders"
        clear_view_cache("/orders")
        page.navigate("/payment")

    def go_payment_from_order(data):
        session["order"] = data
        session["payment"] = None
        session["payment_back_route"] = "/order"
        clear_view_cache("/orders")
        page.navigate("/payment")

    def go_invoice(data):
        session["order"] = data
        page.navigate("/invoice")

    def do_logout(e=None):
        try:
            api.logout()
        except api.ApiError:
            pass
        storage.remove("token")
        storage.remove("user")
        session.clear()
        clear_view_cache()
        page.navigate("/login")

    # ── Per-route view builders ────────────────────────────────────────────
    def _login_view():
        content = build_login_view(
            page,
            storage,
            on_success=lambda user: page.navigate("/"),
        )
        return _wrap(content, "/login")

    def _tab_view(route):
        if route in view_cache:
            return view_cache[route]

        nav = _nav_bar(ROUTE_TO_INDEX[route])
        if route == "/":
            content = build_home_view(page, storage, on_logout=do_logout)
        elif route == "/catalog":
            content = build_catalog_view(page, storage, open_detail)
        elif route == "/cart":
            content = build_cart_view(
                page,
                storage,
                go_checkout,
                go_browse=lambda: page.navigate("/catalog"),
            )
        else:  # /orders
            content = build_orders_view(page, storage, open_order_detail)

        view = _wrap(content, "/", nav=nav)
        view_cache[route] = view
        return view

    def _product_view():
        content = build_product_detail_view(
            page,
            storage,
            session.get("product"),
            on_back=lambda: page.navigate("/catalog"),
        )
        return _wrap(content, "/product")

    def _checkout_view():
        content = build_checkout_view(
            page,
            storage,
            on_back=lambda: page.navigate("/cart"),
            on_success=go_payment_from_checkout,
        )
        return _wrap(content, "/checkout")

    def _payment_view():
        content = build_payment_view(
            page,
            storage,
            session.get("order", {}),
            payment=session.get("payment"),
            on_back=lambda: page.navigate(session.get("payment_back_route", "/orders")),
            on_done=lambda: page.navigate("/orders"),
        )
        return _wrap(content, "/payment")

    def _order_detail_view():
        def on_order_cancelled():
            clear_view_cache("/orders")

        content = build_order_detail_view(
            page,
            storage,
            session.get("order", {}),
            on_back=lambda: page.navigate("/orders"),
            on_pay=go_payment_from_order,
            on_invoice=go_invoice,
            on_cancel=on_order_cancelled,
        )
        return _wrap(content, "/order")

    def _invoice_view():
        content = build_invoice_view(
            page,
            storage,
            session.get("order", {}),
            on_back=lambda: page.navigate("/order"),
        )
        return _wrap(content, "/invoice")

    # ── Routing ────────────────────────────────────────────────────────────
    def route_change(e=None):
        nonlocal current_tab
        route = page.route
        if route == "/login":
            views = [_login_view()]
        else:
            if route in ROUTE_TO_INDEX:
                current_tab = route
            views = [_tab_view(current_tab)]
            # Screens pushed on top of the current tab (skipped when their
            # payload is missing, e.g. after a stale reload/deep link)
            if route == "/product" and session.get("product") is not None:
                views.append(_product_view())
            elif route == "/checkout":
                views.append(_checkout_view())
            elif route == "/payment" and session.get("order"):
                views.append(_payment_view())
            elif route == "/order" and session.get("order"):
                views.append(_order_detail_view())
            elif route == "/invoice" and session.get("order"):
                views.append(_invoice_view())

        page.views.clear()
        page.views.extend(views)
        page.update()

    async def view_pop(e):
        if e.view is None:
            return
        if e.view in page.views:
            page.views.remove(e.view)
        if page.views:
            top = page.views[-1]
            # The tab root always lives at "/" — go back to the real current
            # tab instead of the placeholder route.
            target = current_tab if top.route == "/" else top.route
            await page.push_route(target)

    page.on_route_change = route_change
    page.on_view_pop = view_pop

    # ── Startup ────────────────────────────────────────────────────────────
    def enter_app():
        token = storage.get("token")
        if not token:
            page.route = "/login"
            route_change()
            return
        api.set_token(token)
        try:
            api.orders()
        except api.ApiError as exc:
            if exc.status_code in (401, 403):
                storage.remove("token")
                storage.remove("user")
                page.route = "/login"
                route_change()
                return
        page.route = "/"
        route_change()

    if storage.get("token"):
        enter_app()
    else:
        page.route = "/login"
        route_change()


if __name__ == "__main__":
    ft.run(main)
