import os

from django.http import JsonResponse
from django import forms
from django.forms.models import model_to_dict
from django.conf import settings

from my_admin import member_models
from my_admin import item_models
from ubskin_web_django.common import photo
from ubskin_web_django.common import decorators

class UserCreationForm(forms.ModelForm):
    password1 = forms.CharField(
        error_messages={'required': '不能为空'}
    )
    password2 = forms.CharField(
        error_messages={'required': '密码不能为空'}
    )
    member_name = forms.CharField(
        error_messages={'required': '用户名不能为空'}
    )
    telephone = forms.CharField(
        error_messages={'required': '手机号不能为空'}
    )

    class Meta:
        model = member_models.Member
        fields = ('member_name', 'telephone', 'is_admin')

    def clean_password2(self):
        # Check that the two password entries match
        password1 = self.cleaned_data.get("password1")
        password2 = self.cleaned_data.get("password2")
        if password1 and password2 and password1 != password2:
            raise forms.ValidationError("两次密码不一致")
        return password2

    def clean_member_name(self):
        member_name = self.cleaned_data.get("member_name")
        member = member_models.Member.get_member_by_member_name(member_name)
        if member:
            raise forms.ValidationError("用户名已经存在")
        return member_name

    def clean_telephone(self):
        telephone = self.cleaned_data.get("telephone")
        member = member_models.Member.get_member_by_telephone(telephone)
        if member:
            raise forms.ValidationError("手机号已经被注册")
        return telephone

    def save(self, commit=True):
        # Save the provided password in hashed format
        user = super(UserCreationForm, self).save(commit=False)
        user.set_password(self.cleaned_data["password1"])
        if commit:
            user.save()
        return user

@decorators.api_authenticated
def create_member(request):
    return_value = {
        'status':'error',
        'message':'',
    }
    if request.method == 'POST':
        form = UserCreationForm(request.POST)
        if not form.is_valid():
            return_value['message'] = list(form.errors.values())[0]
            return JsonResponse(return_value)
        form.save()
        return_value['status'] = 'success'
        return JsonResponse(return_value)

@decorators.api_authenticated
def delete_member(request):
    return_value = {
        'status':'error',
        'message':'',
    }
    if request.method == "POST":
        id_list = request.POST.getlist('member_id_list[]')
        member_models.Member.delete_members_by_id_list(id_list)
        return_value['status'] = 'success'
        return JsonResponse(return_value)


@decorators.api_authenticated
def editor_member(request):
    return_value = {
        'status':'error',
        'message':'',
    }
    update_field = ['member_name', 'telephone', 'is_admin']
    member_id = request.GET.get('member_id')
    member_obj = member_models.Member.get_member_by_id(member_id)
    if request.method == 'GET':
        form_data = model_to_dict(member_obj)
        return_value['status'] = 'success'
        return_value['data'] = form_data
        return JsonResponse(return_value)
    else:
        password1 = request.POST.get('password1')
        password2 = request.POST.get('password2')
        if password1 and password2:
            if password1 != password2:
                return_value['message'] = ['两次密码不一致']
                return JsonResponse(return_value)
            member_obj.set_password(password2)
        clear_data = {
            key:request.POST.get(key) for key in update_field 
            if request.POST.get(key)
        }
        clear_data['is_admin'] = True if clear_data['is_admin'] == 'true' else False
        member_models.Member.update_member_by_id(member_id, clear_data)
        return_value['status'] = 'success'
        return JsonResponse(return_value)

@decorators.api_authenticated
def delete_items(request):
    item_id_list = request.POST.getlist('item_id_list[]')
    item_models.Items.delete_item_by_item_ids(item_id_list)
    return JsonResponse({'status': 'success'})

@decorators.api_authenticated
def item_image_create(request):
    return_value = {
        'status':'error',
        'message':'',
    }
    if request.method == "POST":
        files_dict = request.FILES
        image_type = request.POST.get('image_type')
        item_id = request.POST.get('item_id')
        image_type_dict = dict(item_models.ItemImages.type_choces)
        for k in files_dict:
            server_file_path = '/media/photos'
            file_dir = os.path.join(
                settings.MEDIA_ROOT,
                'photos'
            )
            if not os.path.exists(file_dir):
                os.makedirs(file_dir)
            data = photo.save_upload_photo(
                files_dict[k],
                file_dir,
                server_file_path,
                image_type_dict.get(int(image_type))
            )
            if data:
                data.update({
                    'image_type': image_type,
                    'item_id': item_id,
                    'status': 'normal'
                })
                item_models.ItemImages.create_item_image(data)
            else:
                return_value['message'] = '上传失败'
                return JsonResponse(return_value)
        else:
            return_value['result'] = 'success'
            return JsonResponse(return_value)

@decorators.api_authenticated
def delete_item_images(request):
    image_id_list = request.POST.getlist('image_id_list[]')
    item_models.ItemImages. \
        update_images_by_image_id_list(image_id_list, {'status': 'deleted'})
    return JsonResponse({'status': 'success'})

@decorators.api_authenticated
def delete_brands(request):
    if request.method == 'POST':
        brand_ids_list = request.POST.getlist('brand_ids_list[]')
        item_models.Brands.delete_brands_by_id_list(brand_ids_list)
        return JsonResponse({'status': 'success'})

@decorators.api_authenticated
def delete_categories(request):
    if request.method == 'POST':
        categorie_ids_list = request.POST.getlist('categorie_ids_list[]')
        item_models.Categories.delete_categories_by_id_list(categorie_ids_list)
        return JsonResponse({'status': 'success'})

@decorators.api_authenticated
def delete_item_comments(request):
    if request.method == 'POST':
        comment_ids_list = request.POST.getlist('comment_ids_list[]')
        item_models.ItemComments.delete_comment_by_id_list(comment_ids_list)
        return JsonResponse({'status': 'success'})