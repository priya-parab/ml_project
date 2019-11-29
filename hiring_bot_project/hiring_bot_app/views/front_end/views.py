from django.shortcuts import render,redirect
from hiring_bot_app.models.Banner import Banners
from hiring_bot_app.models.candidate import CustomUser
from django.contrib.auth import authenticate, login,logout
from django.contrib import messages
import pandas as pd
from source.prediction import predict,full_data_for_prediction,candidate_data_for_prediction,marks_per_ans
from pandas import read_excel
import json

def base_page(request):
    banner = Banners.objects.all()
    return render(request, 'front_end/home.html', {'banner': banner})

def login_page(request):
    return render(request, 'front_end/login.html')

def logout_view(request):
    logout(request)
    return render(request, 'front_end/login.html')

def Question_set(request):
    email = request.POST.get('email')
    password = request.POST.get('password')
    if CustomUser.objects.filter(email=email).exists():
        user=CustomUser.objects.get(email=email)
        username=user.username
        user = authenticate(request,username=username, password=password)
        if user is not None:
            login(request, user)
            return render(request,'front_end/Question_set.html')
        else:
            messages.error(request, 'Invalid Password')
            return render(request,'front_end/login.html')
    else:
        messages.error(request, 'Invalid Email')
        return render(request, 'front_end/login.html')

def signup(request):
    if request.method == 'POST':
        username = request.POST['username']
        raw_password = request.POST['password']
        email = request.POST['email']
        if CustomUser.objects.filter(username=username).exists():
            messages.error(request,'Username already Exists')
            return redirect('signup')
        elif CustomUser.objects.filter(email=email).exists():
            messages.info(request,'Email already Exists')
            return redirect('signup')
        else:
            user = CustomUser.objects.create_user(username=username, password=raw_password,email=email)
            user.save()
            messages.success(request, 'Signup Successfully')
            return redirect('signup')
    else:
        return render(request, 'front_end/login.html')


def prediction(request):
    with open('candidate/answers/candidate_ans.csv', 'w') as f:
        for index,ans in request.GET.items():
            if ans == '':
                ans = '-'
            answer = ans.replace(',', '')
            f.write("%s,%s\n"%(index,answer))
    full_data_for_prediction()
    predict()
    per_ans_score = marks_per_ans()
    result = read_excel('./candidate/Scores/Score.xlsx')
    new_result = result.rename(columns={'candidate_answer': 'Answers', 'pred': 'Marks'})
    # new_result.to_excel('./log/Score_backup/Score_backup_{}.xlsx'.format(pd.datetime.today().strftime('%y/%m/%d-%H:%M:%S')), sheet_name='Score-card_backup')
    output = new_result.to_json()
    out = json.loads(output)
    with pd.option_context('display.max_colwidth', -1):
        table = new_result.to_html(classes='table',index=False,escape=False)
    mark = per_ans_score['pred'].sum()
    total = len(new_result['Answers'])
    score = (mark / total) * 100
    return render(request,'front_end/score.html',{'score':score,'Marks':mark,'Total':total,'html_table': out,'table':table})

