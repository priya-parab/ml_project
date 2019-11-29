from django.shortcuts import render
from hiring_bot_app.models.Banner import Banners
from hiring_bot_app.models.candidate import CustomUser
from hiring_bot_app.form import CustomUserForm
from django.views.generic import ListView
from django.views.generic.edit import CreateView, UpdateView, DeleteView
from django.urls import reverse_lazy
from django.contrib.messages.views import SuccessMessageMixin
from django.shortcuts import redirect
from django.contrib import messages
from django.views import View
import pandas as pd
import numpy as np
import csv
from sklearn.model_selection import train_test_split
import yaml
import io
import pandas as pd
from django.contrib.auth import authenticate, login,logout
import sys
# from django.contrib.auth.mixins import LoginRequiredMixin

def admin(request):
    return render(request, 'back_end/admin.html')

def train(request):
    train_data = pd.read_csv('recuiter/output_files/qqp_format_final.tsv', sep='\t', header=None)
    training, dev = train_test_split(train_data, test_size=0.2)
    training.to_csv("./recuiter/train-dev-tsv-dataset-for-training/train.tsv", sep='\t', header=None, index=False)
    dev.to_csv("./recuiter/train-dev-tsv-dataset-for-training/dev.tsv", sep='\t', header=None, index=False)

    ## make changes in the global config
    with open("./config/global_config.yml", 'r') as stream:
        global_config = yaml.safe_load(stream)

    global_config['train_bert']['data_dir'] = request.POST.get('data_dir')
    global_config['train_bert']['num_train_epochs'] = request.POST.get('num_train_epochs')
    global_config['train_bert']['output_dir'] = request.POST.get('output_dir')
    global_config['train_bert']['model_file'] = request.POST.get('model_file')
    global_config['inference_bert']['output_model_file'] = request.POST.get('output_model_file')
    with io.open('./config/global_config.yml', 'w', encoding='utf8') as outfile:
        yaml.dump(global_config, outfile, default_flow_style=False, allow_unicode=True)

    ## train model on the recuiter set
    # classifierObj = TrainClassifier()
    # success = classifierObj.main()
    messages.success(request, "Model trained sucessfully")
    return render(request, 'back_end/train_ui.html')

def recruiter_upload_page(request):
    return render(request, 'back_end/recruiter_upload_page.html')

class BannersList(ListView):
    template_name = 'back_end/banners_list.html'
    model = Banners
    paginate_by = 8
    redirect_field_name = 'redirect_to'

class BannersCreate(SuccessMessageMixin, CreateView):
    template_name = 'back_end/banners_create.html'
    # form_class = BannersForm
    model = Banners
    fields = ['name','banner_title', 'banner_path','description']
    success_url = reverse_lazy('banners_list')
    success_message = "%(banner_title)s created successfully"

class BannersUpdate(SuccessMessageMixin, UpdateView):
    # form_class = CategoryForm
    model = Banners
    fields = ['name', 'banner_title', 'banner_path', 'description']
    template_name = 'back_end/banners_edit.html'
    success_url = reverse_lazy('banners_list')
    success_message = "%(banner_title)s updated successfully"


class BannersDelete(SuccessMessageMixin, View):
    def get(self, request, pk):
        query = Banners.objects.get(pk=pk)
        query.delete()
        messages.success(request, "Successfully Deleted ")
        return redirect("banners_list")

    def get_object(self):
        return self.request.user.banner


def convert_to_qqp(request):
    if request.method == "POST":
        my_uploaded_file = request.FILES['my_uploaded_file']
        df_model_ans = pd.read_csv(my_uploaded_file)
        df_model_ans.to_csv('recuiter/output_files/model_ans.csv')
        df_model_ans.drop(['ID', 'Questions'], axis=1, inplace=True)
        result3 = pd.DataFrame(columns=['ans1', 'ans2', 'label'])
        for model_ans_col in df_model_ans:
            first_col = df_model_ans[model_ans_col]
            new_df = df_model_ans
            new_df.drop([model_ans_col], axis=1, inplace=True)
            for each in new_df:
                second_col = new_df[each]
                if each in ['Right_answer2', 'Right_answer3', 'Right_answer4']:
                    third_col = np.ones((20,), dtype=np.int)
                else:
                    third_col = np.zeros((20,), dtype=np.int)
                score = pd.DataFrame(third_col)
                frame = [first_col, second_col, score]
                result2 = pd.concat(frame, axis=1)
                result2.columns = ['ans1', 'ans2', 'label']
                result3 = result3.append(result2)
        result3.to_csv('recuiter/output_files/Shuffled_ans.csv')
        df = pd.read_csv('recuiter/output_files/Shuffled_ans.csv', header=None)
        df = df[1:len(df)]
        ds = df.sample(frac=1)
        ds.insert(1, "ans1_id", range(1, len(ds) + 1))
        ds.insert(2, "ans2_id", range(2, len(ds) + 2))
        ds.reset_index(inplace=True)
        ds.drop(['index', 0], axis=1, inplace=True)
        ds.to_csv('recuiter/output_files/qqp_format.csv', header=False)
        with open('recuiter/output_files/qqp_format.csv', 'r') as csvin, open('recuiter/output_files/qqp_format_final.tsv', 'w') as tsvout:
            csvin = csv.reader(csvin)
            tsvout = csv.writer(tsvout, delimiter='\t')

            for row in csvin:
                tsvout.writerow(row)
        messages.success(request, "File Successfully Uploaded")
    return render(request, 'back_end/recruiter_upload_page.html')

class CustomUserList(ListView ):
    template_name = 'back_end/user_list.html'
    model = CustomUser
    paginate_by = 8
    redirect_field_name = 'redirect_to'

    def password(self,request):
        user_form = CustomUserForm(data=request.POST)
        user = user_form.save()
        user.set_password(user.password)
        user.save()

def CustomUserCreate(request):
    if request.method == 'GET':
        return render(request, 'back_end/user_create.html')
    else:
        form = CustomUserForm(request.POST)
        if form.is_valid():
            CustomUser.objects.create(first_name=request.POST.get("first_name"),last_name=request.POST.get("last_name"),\
                                      email=request.POST.get("email"),username=request.POST.get("email"),password=request.POST.get("password"))
            messages.success(request, "Successfully Added")
            return redirect("user_list")
        else:
            content = {'form': form}
            return render(request, 'back_end/user_create.html', content)


class CustomUserUpdate(SuccessMessageMixin,UpdateView):
    model = CustomUser
    fields = ['first_name', 'last_name','email']
    template_name = 'back_end/user_edit.html'
    success_url = reverse_lazy('user_list')
    success_message = "Successfully Updated"


class CustomUserDelete(SuccessMessageMixin,View):
    def get(self,request,pk):
        query = CustomUser.objects.get(pk=pk)
        query.delete()
        messages.success(request, "Successfully Deleted ")
        return redirect("user_list")

def train_page(request):
    return render(request, 'back_end/train_ui.html')

def admin_login_page(request):
    return render(request, 'back_end/login.html')

def admin_login(request):
    if request.method=="POST" :
        email = request.POST.get('email')
        password = request.POST.get('password')
        if CustomUser.objects.filter(email=email).exists():
            username=CustomUser.objects.get(email=email)
            user = authenticate(request,username=username, password=password)
            if user is not None:
                login(request, user)
                return redirect('admin')
            else:
                messages.error(request, 'Invalid Password')
                return render(request,'back_end/login.html')
        else:
            messages.error(request, 'Invalid Email')
    return render(request, 'back_end/login.html')


def admin_logout(request):
    logout(request)
    return render(request, 'back_end/login.html')