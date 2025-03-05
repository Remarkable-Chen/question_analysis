# -*- coding: utf-8 -*-
"""
Created on Tue Mar  4 11:04:38 2025

@author: kaixiang.chen
"""
import os
from asammdf import MDF
import tkinter as tk
from tkinter import Tk, Label, Entry, Button, Checkbutton, IntVar, StringVar, font,filedialog,messagebox,Listbox,Scrollbar,scrolledtext
import datetime


def Lat_to_one_side(file_path, AgCtrlTqUpprLim_name, AsyLatOffstSts_name, TurnIndicReqByALCA_name,
                   LaneMkrLe_name, LaneMkrRi_name):
    
    def get_signal_safe(mdf, name):
        postion = mdf.whereis(name)
        (first_value, second_value) = postion[0]
        return mdf.get(name, first_value, second_value)
    
    mdf = MDF(file_path)
    start_time = mdf.header.start_time
    
    # 获取所有信号
    signals = [
        get_signal_safe(mdf, AgCtrlTqUpprLim_name),
        get_signal_safe(mdf, AsyLatOffstSts_name),
        get_signal_safe(mdf, TurnIndicReqByALCA_name),
        get_signal_safe(mdf, LaneMkrLe_name),
        get_signal_safe(mdf, LaneMkrRi_name)
    ]
    
    # 重采样对齐时间轴
    resampled_mdf = MDF()
    resampled_mdf.append(signals)
    resampled_mdf = resampled_mdf.resample(raster=0.1)  # 100ms采样
    
    # 获取重采样信号
    AgCtrl = resampled_mdf.get(AgCtrlTqUpprLim_name)
    AsyLat = resampled_mdf.get(AsyLatOffstSts_name)
    TurnIndic = resampled_mdf.get(TurnIndicReqByALCA_name)
    LaneLe = resampled_mdf.get(LaneMkrLe_name)
    LaneRi = resampled_mdf.get(LaneMkrRi_name)
    
    # 统计结果存储
    condition1_events = []  # 条件1满足时间段
    condition2_events = []  # 条件2满足时间段
    
    # 状态跟踪变量
    cond1_start = None
    cond2_start = None
    
    for i in range(len(AgCtrl)):
        # 通用条件
        common_cond = (AgCtrl.samples[i] == 3 and 
                      TurnIndic.samples[i] == b'IndcrTypExt1_Off')
        
        # 条件1判断
        cond1 = (common_cond and 
                AsyLat.samples[i] == 0 and 
                (LaneLe.samples[i] - abs(LaneRi.samples[i])) > 0.4)
        
        # 条件2判断
        cond2 = (common_cond and 
                AsyLat.samples[i] != 0 and 
                (LaneLe.samples[i] - abs(LaneRi.samples[i])) > 0.8)
        
        # 处理条件1
        if cond1:
            if cond1_start is None:
                cond1_start = AgCtrl.timestamps[i]
        else:
            if cond1_start is not None:
                duration = AgCtrl.timestamps[i] - cond1_start
                if duration >= 3:
                    start_abs = start_time + datetime.timedelta(seconds=cond1_start)
                    end_abs = start_time + datetime.timedelta(seconds=AgCtrl.timestamps[i])
                    condition1_events.append((start_abs, end_abs, duration))
                cond1_start = None
                
        # 处理条件2
        if cond2:
            if cond2_start is None:
                cond2_start = AgCtrl.timestamps[i]
        else:
            if cond2_start is not None:
                duration = AgCtrl.timestamps[i] - cond2_start
                if duration >= 3:
                    start_abs = start_time + datetime.timedelta(seconds=cond2_start)
                    end_abs = start_time + datetime.timedelta(seconds=AgCtrl.timestamps[i])
                    condition2_events.append((start_abs, end_abs, duration))
                cond2_start = None
                
    # 处理文件末尾可能未结束的条件
    if cond1_start is not None:
        duration = AgCtrl.timestamps[-1] - cond1_start
        if duration >= 3:
            start_abs = start_time + datetime.timedelta(seconds=cond1_start)
            end_abs = start_time + datetime.timedelta(seconds=AgCtrl.timestamps[-1])
            condition1_events.append((start_abs, end_abs, duration))
            
    if cond2_start is not None:
        duration = AgCtrl.timestamps[-1] - cond2_start
        if duration >= 3:
            start_abs = start_time + datetime.timedelta(seconds=cond2_start)
            end_abs = start_time + datetime.timedelta(seconds=AgCtrl.timestamps[-1])
            condition2_events.append((start_abs, end_abs, duration))
            
    return {
        "condition1": condition1_events,
        "condition2": condition2_events
    }

def lat_press_line(file_path, AgCtrlTqUpprLim_name, SwtIndcrIndcrTypExtReq_name,
                  TurnIndicReqByALCA_name, AsySteerWhlHptcWarnReq_name, LaneChgWarnSts_name):
    
    def get_signal_safe(mdf, name):
        postion = mdf.whereis(name)
        (first_value, second_value) = postion[0]
        return mdf.get(name,first_value, second_value)
    
    mdf = MDF(file_path)
    
    # 获取原始信号
    signals = [
        get_signal_safe(mdf, AgCtrlTqUpprLim_name),
        get_signal_safe(mdf, SwtIndcrIndcrTypExtReq_name),
        get_signal_safe(mdf, TurnIndicReqByALCA_name),
        get_signal_safe(mdf, AsySteerWhlHptcWarnReq_name),
        get_signal_safe(mdf, LaneChgWarnSts_name)
    ]
    
    # 创建新MDF用于重采样
    resampled_mdf = MDF()
    resampled_mdf.append(signals)
    
    # 使用明确采样率（示例使用10ms）
    resampled_mdf = resampled_mdf.resample(raster=0.01)
    
    # 获取重采样后的信号
    AgCtrl_resampled = resampled_mdf.get(AgCtrlTqUpprLim_name)
    SwtIndcr_resampled = resampled_mdf.get(SwtIndcrIndcrTypExtReq_name)
    TurnIndic_resampled = resampled_mdf.get(TurnIndicReqByALCA_name)
    AsySteer_resampled = resampled_mdf.get(AsySteerWhlHptcWarnReq_name)
    LaneChg_resampled = resampled_mdf.get(LaneChgWarnSts_name)
    
    # 新增：获取文件起始时间
    start_time = mdf.header.start_time
    
    # 修改计数器为时间戳列表
    press_times = []
    
    # 从第1个点开始检查（避免i-1越界）
    for i in range(1, len(AgCtrl_resampled)):
        condition1 = AgCtrl_resampled.samples[i] == 3
        condition2 = SwtIndcr_resampled.samples[i] == b'IndcrTypExt1_Off'
        condition3 = TurnIndic_resampled.samples[i] == b'IndcrTypExt1_Off'
        condition4 = (AsySteer_resampled.samples[i] == b'OnOff1_On' and 
                     AsySteer_resampled.samples[i-1] == b'OnOff1_Off')
        
        if all([condition1, condition2, condition3, condition4]):
            # 计算绝对时间
            relative_time = AgCtrl_resampled.timestamps[i]
            absolute_time = start_time + datetime.timedelta(seconds=relative_time)
            
            # 修改去重逻辑的时间差计算
            min_interval = 1.0  # 最小触发间隔1秒
            if press_times:
                time_diff = (absolute_time - press_times[-1]).total_seconds()
                if time_diff < min_interval:
                    continue
            press_times.append(absolute_time)
            
    return press_times

def mf4_folder_directory():
    # 使用filedialog的askdirectory方法来弹出目录选择对话框
    entry_mf4_folder_selected = filedialog.askdirectory()
    
    # 如果用户选择了一个目录，就在entry中显示这个目录的路径
    if entry_mf4_folder_selected:
        entry_mf4_folder.delete(0, tk.END)  # 清空entry中的内容
        entry_mf4_folder.insert(0, entry_mf4_folder_selected)  # 插入选择的目录路径
        
def process_folder_a():
    # 信号名称配置
    lane_signals = {
        'AgCtrlTqUpprLim_name': 'AgCtrlTqUpprLim',
        'AsyLatOffstSts_name': 'AsyLatOffstSts',
        'TurnIndicReqByALCA_name': 'TurnIndicReqByALCA',
        'LaneMkrLe_name': 'P_RGF_Bus_LaneMkr_s_LaneMkr1Vcc_t.ClsLe.LaneMkrEstimn1Vcc.DstLatConCoeffFirst',
        'LaneMkrRi_name': 'P_RGF_Bus_LaneMkr_s_LaneMkr1Vcc_t.ClsRi.LaneMkrEstimn1Vcc.DstLatConCoeffFirst'
    }
    
    for filename in os.listdir(entry_mf4_folder.get()):
        if filename.endswith('.mf4'):
            file_path = os.path.join(entry_mf4_folder.get(), filename)
            
            result = Lat_to_one_side(file_path, **lane_signals)
            
            # 输出结果
            print(f"文件 {filename} 分析结果：")
            print("横向偏一侧满足条件1：")
            for start, end, duration in result['condition1']:
                print(f"  {start} ~ {end} 持续{duration:.1f}秒")
                
            print("横向偏一侧满足条件2：")
            for start, end, duration in result['condition2']:
                print(f"  {start} ~ {end} 持续{duration:.1f}秒")
                
def process_folder_b():
    # 信号名称定义
    AgCtrlTqUpprLim_name = 'AgCtrlTqUpprLim'
    SwtIndcrIndcrTypExtReq_name = 'SwtIndcrIndcrTypExtReq'
    TurnIndicReqByALCA_name = 'TurnIndicReqByALCA'
    AsySteerWhlHptcWarnReq_name = 'AsySteerWhlHptcWarnReq'
    LaneChgWarnSts_name = 'LaneChgWarnSts'  # 新增信号
    
    for filename in os.listdir(entry_mf4_folder.get()):
        if filename.endswith('.mf4'):
            file_path = os.path.join(entry_mf4_folder.get(), filename)
            
            press_times = lat_press_line(
                file_path,
                AgCtrlTqUpprLim_name,
                SwtIndcrIndcrTypExtReq_name,
                TurnIndicReqByALCA_name,
                AsySteerWhlHptcWarnReq_name,
                LaneChgWarnSts_name
            )
            
            # 转换时间为可读格式
            time_str = "\n".join([t.strftime("%Y-%m-%d %H:%M:%S.%f")[:-3] for t in press_times])
            print(f"文件 {filename} 压线触发时刻：{time_str}")


def processing():
    compress_a = bool(check_var1.get())
    compress_b = bool(check_var2.get())
    if compress_a:
        process_folder_a()
    elif compress_b:
        process_folder_b()
    else:    
        messagebox.showinfo("提示", "请先勾选需要实现的功能")
        
window = Tk()
window.title('横向问题数据处理v1.0')
window.geometry("920x170")
default_font = font.nametofont("TkDefaultFont")
default_font.config(size=int(default_font.cget("size") * 1.5))
window.option_add("*Font", default_font)


Label(window, text='请输入mf4文件夹全路径:').grid(row=1, column=0, sticky='w', pady=4, padx=4)
entry_mf4_folder = Entry(window)
entry_mf4_folder.grid(row=1, column=1, sticky='ew', pady=4, padx=4)
Button1 = Button(window, text="选择目录", command=mf4_folder_directory,font=("TkDefaultFont", 10)).grid(row=1, column=2, sticky='e', pady=0.5, padx=0.5)

check_var1 = IntVar(value=0)
checkbox_compress = Checkbutton(window, text='横向偏一侧', variable=check_var1)
checkbox_compress.grid(row=2, column=0, sticky='w', pady=4, padx=4, columnspan=2)    

check_var2 = IntVar(value=0)
checkbox_upload = Checkbutton(window, text='横向压线', variable=check_var2)
checkbox_upload.grid(row=2, column=1, sticky='w', pady=4, padx=4, columnspan=2)

submit_button = Button(window, text="提交", command=processing)
submit_button.grid(row=11, column=0, columnspan=2, pady=8, padx=4)
submit_button.config(height=int(submit_button.cget('height') * 1.5), width=int(submit_button.cget('width') * 1.5))

window.grid_columnconfigure(1, weight=2)
window.mainloop()