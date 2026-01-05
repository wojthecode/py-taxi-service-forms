from turtle import mode
from django.contrib.auth.decorators import login_required
from django.http import HttpRequest, HttpResponse, HttpResponseRedirect
from django.shortcuts import render
from django.urls import reverse, reverse_lazy
from django.views import generic
from django.contrib.auth.mixins import LoginRequiredMixin

from taxi.models import Driver, Car, Manufacturer


@login_required
def index(request: HttpRequest) -> HttpResponse:
    """View function for the home page of the site."""

    num_drivers = Driver.objects.count()
    num_cars = Car.objects.count()
    num_manufacturers = Manufacturer.objects.count()

    num_visits = request.session.get("num_visits", 0)
    request.session["num_visits"] = num_visits + 1

    context = {
        "num_drivers": num_drivers,
        "num_cars": num_cars,
        "num_manufacturers": num_manufacturers,
        "num_visits": num_visits + 1,
    }

    return render(request, "taxi/index.html", context=context)


class ManufacturerListView(LoginRequiredMixin, generic.ListView):
    model = Manufacturer
    context_object_name = "manufacturer_list"
    template_name = "taxi/manufacturer_list.html"
    paginate_by = 5


class ManufacturerCreateView(LoginRequiredMixin, generic.CreateView):
    model = Manufacturer
    fields = "__all__"
    success_url = reverse_lazy("taxi:manufacturer-list")
    template_name = "taxi/manufacturer_form.html"


class ManufacturerUpdateView(LoginRequiredMixin, generic.UpdateView):
    model = Manufacturer
    fields = "__all__"
    success_url = reverse_lazy("taxi:manufacturer-list")
    template_name = "taxi/manufacturer_form.html"


class ManufacturerDeleteView(LoginRequiredMixin, generic.DeleteView):
    model = Manufacturer
    template_name = "taxi/confirm_delete.html"
    success_url = reverse_lazy("taxi:manufacturer-list")


class CarListView(LoginRequiredMixin, generic.ListView):
    model = Car
    paginate_by = 5
    queryset = Car.objects.all().select_related("manufacturer")


class CarDetailView(LoginRequiredMixin, generic.DetailView):
    model = Car


@login_required
def car_create_view(request: HttpRequest) -> HttpResponse:
    context = {}
    if request.method == "POST":
        model = request.POST["model"]
        manufacturer = request.POST["manufacturer"]
        drivers = request.POST.getlist("drivers")

        if isinstance(model, str) and len(model) > 0:
            new_car = Car.objects.create(
                model=model, manufacturer_id=manufacturer
            )
            if drivers:
                new_car.drivers.set(drivers)
            return HttpResponseRedirect(
                reverse("taxi:car-detail", args=[new_car.pk])
            )
        context["error"] = "* This field is required!"
        context["car_manufacturer"] = int(manufacturer)
        context["car_drivers"] = list(map(int, drivers))

    context["manufacturers"] = Manufacturer.objects.all()
    context["drivers"] = Driver.objects.all()
    return render(request, "taxi/car_form.html", context=context)


@login_required
def car_update_view(request: HttpRequest, pk: int) -> HttpResponse:

    car = Car.objects.prefetch_related("drivers").get(id=pk)
    context = {}

    if request.method == "POST":
        model = request.POST["model"]
        manufacturer = request.POST["manufacturer"]
        drivers = request.POST.getlist("drivers")

        if isinstance(model, str) and len(model) > 0:
            car.model = model
            car.manufacturer.pk = manufacturer
            car.drivers.set(drivers)
            car.save()
            return HttpResponseRedirect(
                reverse("taxi:car-detail", args=[car.pk])
            )

        context["error"] = "* This field is required!"
        car_manufacturer = int(manufacturer)
        car_drivers = list(map(int, drivers))

    else:
        model = car.model
        car_manufacturer = car.manufacturer.pk
        car_drivers = [*car.drivers.values_list("id", flat=True)]
        pass

    manufacturers = Manufacturer.objects.all()
    drivers = Driver.objects.all()

    context |= {
        "car_model": model,
        "car_manufacturer": car_manufacturer,
        "car_drivers": car_drivers,
        "manufacturers": manufacturers,
        "drivers": drivers,
        "update": True,
    }

    print([*car.drivers.values_list("id", flat=True)])

    return render(request, "taxi/car_form.html", context=context)


@login_required
def car_delete_view(request: HttpRequest, pk: int) -> HttpResponse:
    if request.method == "POST":
        car = Car.objects.get(id=pk)
        car.delete()
        return HttpResponseRedirect(reverse("taxi:car-list"))
    context = {"pk": pk}
    return render(request, "taxi/confirm_delete.html", context=context)


class DriverListView(LoginRequiredMixin, generic.ListView):
    model = Driver
    paginate_by = 5


class DriverDetailView(LoginRequiredMixin, generic.DetailView):
    model = Driver
    queryset = Driver.objects.all().prefetch_related("cars__manufacturer")
