import yaml
from run_prediction import Inference
import pandas as pd
from pandas import read_excel


def inference_output():
    with open("config/global_config.yml", "r") as filename:
        config = yaml.load(filename)
        output_model_file = config["inference_bert"]["output_model_file"]
        bert_model= config["inference_bert"]["bert_model"]
        max_seq_length = config["inference_bert"]["max_seq_length"]
        with open(config["inference_bert"]["labels"], 'r') as read_file:
            labels = list(map(lambda x: x.strip('\n'), read_file.readlines()))
            num_labels = len(labels)

    prediction_obj = Inference(bert_model=bert_model, num_labels=num_labels, labels=labels,output_model_file = output_model_file, max_seq_length = max_seq_length )
    return prediction_obj

def predict():
    prediction_obj = inference_output()
    excel_path = './candidate/full_data_for_prediction/full_data.xlsx'
    result_df = []
    df_correct = pd.read_excel(open(excel_path, 'rb'), sheetname='correct-dataset')
    df_candidate = pd.read_excel(open(excel_path, 'rb') , sheetname='candidate-dataset')
    answer_rows = list(df_correct.columns)
    answer_rows.remove('Questions')
    answer_rows.remove('Index')
    for c_index, candidate_row in df_candidate.iterrows():
    	candidate_ans = ''
    	question_index = candidate_row['Index']
    	candidate_ans = candidate_row['candidate_ans']
    	for correct_index, correct_row in df_correct.iterrows():
    		correct_ans_index = correct_row['Index']
    		if question_index == correct_ans_index:
    			for each_ans in answer_rows:
    				model_ans = ''
    				model_ans = correct_row[each_ans]
    				inter_result = {"candidate_answer" : candidate_ans, "model_answer" : model_ans}
    				inter_result['pred'] , inter_result['probabilty'] = prediction_obj.main(inter_result)
    				result_df.append(inter_result)
    result_df = pd.DataFrame(result_df)
    result_df.to_excel("./candidate/predicted_output/prediction.xlsx", sheet_name='prediction')
    # result_df.to_excel("./log/predicted_output_backup/prediction_{}.xlsx".format(pd.datetime.today().strftime('%y/%m/%d-%H:%M:%S')))


def candidate_data_for_prediction():
    df_model_ans = pd.read_csv('recuiter/output_files/model_ans.csv')
    df_quest = df_model_ans[['Questions']]
    df_candidate_ans = pd.read_csv('candidate/answers/candidate_ans.csv', names=['Index', 'candidate_ans'])
    df_candidate_ans['Index'] = range(1, len(df_candidate_ans) + 1)
    df_candidate_ans.insert(1, 'Questions', df_quest.iloc[0:len(df_candidate_ans) + 1])
    df_candidate_answer = df_candidate_ans[['Index', 'Questions', 'candidate_ans']]
    return df_candidate_answer

def marks_per_ans():
    df_model_ans = pd.read_csv('recuiter/output_files/model_ans.csv')
    df_quest = df_model_ans[['Questions']]
    right_ans = []
    list_col_model_ans = df_model_ans.columns
    for col in list_col_model_ans:
        if 'Right_answer' in col:
            right_ans.append(col)
    df_right_ans = df_model_ans[right_ans]
    right_ans_col_len = len(df_right_ans.columns)
    df = read_excel('./candidate/predicted_output/prediction.xlsx')
    five_ques = df_quest.iloc[0:len(candidate_data_for_prediction())]
    five_ques = five_ques['Questions'].values.tolist()
    quest_list = []
    for q in five_ques:
        for n in range(right_ans_col_len):
            quest_list.append(q)

    data = df[['candidate_answer', 'pred']]
    data.insert(0, 'Questions', quest_list)
    per_ans_score = data.groupby(['Questions', 'candidate_answer'], sort=False).sum()
    per_ans_score.loc[per_ans_score.pred > 0, 'pred'] = 1
    per_ans_score.to_excel('./candidate/Scores/Score.xlsx', sheet_name='Score-card')
    return per_ans_score

def right_answer_data_for_prediction():
    df_model_ans = pd.read_csv('recuiter/output_files/model_ans.csv')
    df_quest = df_model_ans[['Questions']]
    right_ans = []
    list_col_model_ans = df_model_ans.columns
    for col in list_col_model_ans:
        if 'Right_answer' in col:
            right_ans.append(col)
    df_right_ans = df_model_ans[right_ans]
    df_right_ans = df_right_ans.reset_index()
    df_right_answer = df_right_ans.drop(['index'], axis=1)
    df_right_answer.insert(0,'Index',range(1,len(df_quest)+1))
    df_right_answer.insert(1, 'Questions', df_quest.iloc[0:len(df_quest)+1])
    return df_right_answer

def full_data_for_prediction():
    df_candidate_answer = candidate_data_for_prediction()
    df_right_answer = right_answer_data_for_prediction()
    writer = pd.ExcelWriter('./candidate/full_data_for_prediction/full_data.xlsx',engine='xlsxwriter')
    df_right_answer.to_excel(writer, sheet_name='correct-dataset')
    df_candidate_answer.to_excel(writer, sheet_name='candidate-dataset')
    writer.save()