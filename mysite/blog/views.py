from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger
from django.core.mail import send_mail
from django.shortcuts import get_object_or_404, render
from django.views.generic import ListView
from django.views.decorators.http import require_POST

from blog.models import Comment, Post
from blog.forms import CommentForm, EmailPostForm


def post_list(request):
    post_list = Post.published.all()
    # Постраничная разбивка с 3 постами на страницу
    paginator = Paginator(post_list, 2)
    page_number = request.GET.get('page', 1)
    try:
        posts = paginator.page(page_number)
    except PageNotAnInteger:
        # Если page_number не число,
        # то выдать первую страницу
        posts = paginator.page(1)
    except EmptyPage:
        # Если page_number вне диапозона,
        # то выдать последнюю страницу
        posts = paginator.page(paginator.num_pages)
    return render(request,
                  'blog/post/list.html',
                  {'posts': posts})


def post_detail(request, year, month, day, post):
    post = get_object_or_404(Post,
                             status=Post.Status.PUBLISHED,
                             slug=post,
                             publish__year=year,
                             publish__month=month,
                             publish__day=day)
    return render(request, 'blog/post/detail.html', {'post': post})


class PostListView(ListView):
    queryset = Post.published.all()
    context_object_name = 'posts'
    paginate_by = 3
    template_name = 'blog/post/list.html'


def post_share(request, post_id):
    # Получить пост по id
    post = get_object_or_404(
        Post, id=post_id,
        status=Post.Status.PUBLISHED)
    sent = False

    if request.method == 'POST':
        # Форма передана на обработку
        form = EmailPostForm(request.POST)
        if form.is_valid():
            # Форма прошла валидацию успешно
            cd = form.cleaned_data
            post_url = request.build_absolute_uri(post.get_absolute_url())
            subject = f"{cd['name']} recommends you read " \
                      f"{post.title}"
            message = f"Read {post.title} at {post_url}\n\n" \
                      f"{cd['name']}\'s comments: {cd['comments']}"
            send_mail(subject, message, 'my_account@gmail.com',
                      [cd['to']])
            sent = True
    else:
        form = EmailPostForm()
    return render(request, 'blog/post/share.html', {'post': post,
                                                    'form': form,
                                                    'sent': sent})


@require_POST
def post_comment(request, post_id):
    post = get_object_or_404(
        Post, id=post_id, status=Post.Status.PUBLISHED
        )
    comment = None
    # Комментарий был отправлен
    form = CommentForm(data=request.POST)
    if form.is_valid():
        # Создать объект комментария не сохраняя в бд.
        comment = form.save(commit=False)
        # Установить значение поста.
        comment.post = post
        # Сохранить коммент в бд.
        comment.save()
    return render(request, 'blog/post/comment.html',
                           {'post': post,
                            'form': form,
                            'comment': comment})
