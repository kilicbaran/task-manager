from django.shortcuts import render, redirect
from django.urls import reverse
from django.db.models import Q
from .models import Task, Tag
import datetime


def index(request):
    task_list = Task.objects.filter(archive_date__isnull=True)

    today = datetime.date.today()
    in_a_week = today + datetime.timedelta(days=7)
    in_a_month = today + datetime.timedelta(days=30)

    task_list_no_deadline = task_list.filter(deadline=None)
    task_list_late = task_list.filter(deadline__date__lt=today)
    task_list_today = task_list.filter(deadline__date=today)
    task_list_week = task_list.filter(deadline__date__gt=today, deadline__date__lte=in_a_week)
    task_list_month = task_list.filter(deadline__date__gt=in_a_week, deadline__date__lte=in_a_month)
    task_list_other = task_list.filter(deadline__date__gt=in_a_month)

    context = {'task_list': task_list, 'task_list_no_deadline': task_list_no_deadline, 'task_list_late': task_list_late,
               'task_list_today': task_list_today, 'task_list_week': task_list_week, 'task_list_month': task_list_month,
               'task_list_other': task_list_other}
    return render(request, 'app/index.html', context)


def add(request):
    if request.method == "POST":
        if "task_add" in request.POST:
            description = request.POST["description"]
            str_deadline = str(request.POST["deadline"])  # print(deadline) # output: 2018-06-30
            if str_deadline == "":  # if no deadline is specified
                deadline = None  # this sets the deadline field to NULL
            else:
                int_deadline = [int(x) for x in str_deadline.split("-")]
                deadline = datetime.datetime(int_deadline[0], int_deadline[1], int_deadline[2])
            todo = Task(description=description, deadline=deadline, archive_date=None)
            todo.save()
            tags = request.POST["tags"].replace(" ", "").split(",")
            for tag_text in tags:
                if not Tag.objects.filter(text=tag_text).exists():
                    new_tag = Tag(text=tag_text)
                    new_tag.save()
                    new_tag.tasks.add(todo)
                else:
                    Tag.objects.get(text=tag_text).tasks.add(todo)
        previous_url = request.POST["previous_url"]
        if previous_url:
            return redirect(previous_url)
        else:
            return redirect(reverse('app:index'))
    previous_url = request.META.get('HTTP_REFERER')
    context = {'previous_url': previous_url}
    return render(request, 'app/add.html', context)


def edit(request):
    if request.method == "POST":
        if "task_edit" in request.POST:
            task_id = request.POST["task_id"]
            todo = Task.objects.get(id=int(task_id))
            todo.tag_set.clear()
            todo.description = request.POST["description"]

            str_deadline = str(request.POST["deadline"])  # print(deadline) # output: 2018-06-30
            if str_deadline == "":  # if no deadline is specified
                deadline = None  # this sets the deadline field to NULL
            else:
                int_deadline = [int(x) for x in str_deadline.split("-")]
                deadline = datetime.datetime(int_deadline[0], int_deadline[1], int_deadline[2])
            todo.deadline = deadline
            todo.save()
            tags = request.POST["tags"].replace(" ", "").split(",")
            for tag_text in tags:
                if not Tag.objects.filter(text=tag_text).exists():
                    new_tag = Tag(text=tag_text)
                    new_tag.save()
                    new_tag.tasks.add(todo)
                else:
                    Tag.objects.get(text=tag_text).tasks.add(todo)
            previous_url = request.POST["previous_url"]
            if previous_url:
                return redirect(previous_url)
            else:
                return redirect(reverse('app:index'))
        else:
            task_id = request.POST["task_id"]
            todo = Task.objects.get(id=int(task_id))
            tags = todo.tag_set.all()
            tag_text = ""
            for a_tag in tags:
                tag_text += a_tag.text + ","
            if tag_text.endswith(","):
                tag_text = tag_text[:-1]
            previous_url = request.META.get('HTTP_REFERER')
            context = {'task': todo, 'tag_text': tag_text, 'previous_url': previous_url}
            return render(request, 'app/edit.html', context)


def delete(request):
    if request.method == "POST":
        if "task_delete" in request.POST:
            task_id = request.POST["task_id"]
            todo = Task.objects.get(id=int(task_id))
            for a_tag in todo.tag_set.all():
                if a_tag.tasks.count() == 1:
                    a_tag.delete()
            todo.tag_set.clear()
            todo.delete()
    previous_url = request.META.get('HTTP_REFERER')
    if previous_url:
        return redirect(previous_url)
    else:
        return redirect(reverse('app:index'))


def archive_toggle(request):
    if request.method == "POST":
        task_id = request.POST["task_id"]
        todo = Task.objects.get(id=int(task_id))
        if todo.archive_date is None:
            todo.archive_date = datetime.datetime.now()
        else:
            todo.archive_date = None
        todo.save()
    previous_url = request.META.get('HTTP_REFERER')
    if previous_url:
        return redirect(previous_url)
    else:
        return redirect(reverse('app:index'))


def search(request):
    if request.method == "GET":
        query = request.GET["query"]
        query_list = query.split(" ")
        keyword_list = [token for token in query_list if not token.startswith("tag:")]
        tag_list = [token.split(":")[1] for token in query_list if token.startswith("tag:")]
        task_list = Task.objects.all()
        for tag_text in tag_list:
            tag_object = Tag.objects.get(text=tag_text)
            task_list &= tag_object.tasks.all()
        q_objects = Q()  # init our q objects variable to use .add() on it
        for item in keyword_list:  # loop trough the list and create an OR condition for each item
            q_objects.add(Q(description__icontains=item), Q.OR)
        task_list = task_list.filter(q_objects)
        task_list_not_archived = task_list.filter(archive_date__isnull=True)
        task_list_archived = task_list.filter(archive_date__isnull=False)
        context = {'task_list_not_archived': task_list_not_archived, 'task_list_archived': task_list_archived,
                   'query': query}
        return render(request, 'app/search.html', context)
    return redirect(reverse('app:index'))


def archived(request):
    task_list = Task.objects.filter(archive_date__isnull=False).order_by('-archive_date')
    context = {'task_list': task_list}
    return render(request, 'app/archived.html', context)


def clear(request):
    task_list = Task.objects.all()
    for task in task_list:
        task.tag_set.clear()
    Task.objects.all().delete()
    Tag.objects.all().delete()
    return redirect(reverse('app:index'))


def student(request):
    task_list = Task.objects.all()
    for task in task_list:
        task.tag_set.clear()
    Task.objects.all().delete()
    Tag.objects.all().delete()

    today = datetime.date.today()

    exam_tag = Tag(text="exam")
    exam_tag.save()
    math_tag = Tag(text="math")
    math_tag.save()
    physics_tag = Tag(text="physics")
    physics_tag.save()
    chemistry_tag = Tag(text="chemistry")
    chemistry_tag.save()
    biology_tag = Tag(text="biology")
    biology_tag.save()

    task = Task(description="Math exam", deadline=(today + datetime.timedelta(days=2)))
    task.save()
    exam_tag.tasks.add(task)
    math_tag.tasks.add(task)
    task = Task(description="Math 2nd exam", deadline=(today + datetime.timedelta(days=32)))
    task.save()
    exam_tag.tasks.add(task)
    math_tag.tasks.add(task)
    task = Task(description="Physics exam", deadline=(today + datetime.timedelta(days=9)))
    task.save()
    exam_tag.tasks.add(task)
    physics_tag.tasks.add(task)
    task = Task(description="Chemistry exam", deadline=(today - datetime.timedelta(days=4)),
                archive_date=(today - datetime.timedelta(days=4)))
    task.save()
    exam_tag.tasks.add(task)
    chemistry_tag.tasks.add(task)
    task = Task(description="University entrance exam", deadline=(today + datetime.timedelta(days=60)))
    task.save()
    exam_tag.tasks.add(task)

    task = Task(description="Do math homework page 123", deadline=today)
    task.save()
    math_tag.tasks.add(task)
    task = Task(description='Return harry potter "the goblet of fire" to library',
                deadline=(today - datetime.timedelta(days=1)))
    task.save()
    task = Task(description='Read harry potter "the order of the phoenix"')
    task.save()
    task = Task(description="Complete English project", deadline=(today + datetime.timedelta(days=12)))
    task.save()
    task = Task(description="Do biology homework", deadline=(today + datetime.timedelta(days=3)))
    task.save()
    biology_tag.tasks.add(task)

    task = Task(description="Solve 4 math tests", deadline=(today + datetime.timedelta(days=5)))
    task.save()
    math_tag.tasks.add(task)
    task = Task(description="Solve 2 history tests", deadline=(today + datetime.timedelta(days=7)))
    task.save()
    task = Task(description="Solve 3 physics tests", deadline=(today - datetime.timedelta(days=2)),
                archive_date=(today - datetime.timedelta(days=2)))
    task.save()
    physics_tag.tasks.add(task)
    task = Task(description="Solve 3 biology tests", deadline=(today - datetime.timedelta(days=3)),
                archive_date=(today - datetime.timedelta(days=3)))
    task.save()
    biology_tag.tasks.add(task)
    task = Task(description="Solve 4 chemistry tests", deadline=(today - datetime.timedelta(days=7)),
                archive_date=(today - datetime.timedelta(days=7)))
    task.save()
    chemistry_tag.tasks.add(task)
    task = Task(description="Solve 2 math tests", deadline=(today - datetime.timedelta(days=10)),
                archive_date=(today - datetime.timedelta(days=10)))
    task.save()
    math_tag.tasks.add(task)
    return redirect(reverse('app:index'))
