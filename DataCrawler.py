import requests
import pandas as pd
from datetime import datetime, timedelta
import warnings
import time

# 忽略警告
warnings.filterwarnings('ignore')

class DataCrawler:
    """数据爬取核心类"""
    def __init__(self):
        # 定义API端点
        self.url_dict = {
            "统调负荷": "https://spot.poweremarket.com/uptspot/ma/spot/spottrade/scptp/sr/mp/spottrade/intePublishDayAutotuneCurve/getObj",
            "非市场化机组出力": "https://spot.poweremarket.com/uptspot/ma/spot/spottrade/scptp/sr/mp/spottrade/intePublishNonmarketUnitCurve/getList",
            "非市场机组电源不含新能源总出力预测":"https://spot.poweremarket.com/uptspot/ma/spot/spottrade/scptp/sr/mp/spottrade/mkXhNonMarketEleNewPowerPre/getList",
            "新能源总出力": "https://spot.poweremarket.com/uptspot/ma/spot/spottrade/scptp/sr/mp/spottrade/intePublishNewEnergyDay/getList",
            "正备用": "https://spot.poweremarket.com/uptspot/ma/spot/spottrade/scptp/sr/mp/spottrade/intePublishPositiveNegative/getListPage",
            "负备用": "https://spot.poweremarket.com/uptspot/ma/spot/spottrade/scptp/sr/mp/spottrade/intePublishPositiveNegative/getListPage",
            "西电东送": "https://spot.poweremarket.com/uptspot/ma/spot/spottrade/scptp/sr/mp/spottrade/spotTpaTransSection/getSectionCollectList",
            "日前交易结果查询（发电侧）": "https://spot.poweremarket.com/uptspot/ma/spot/spottrade/scptp/sr/mp/spottrade/tdSpotRecentlyResultGenInfo/getList",
            "实时交易结果查询（发电侧）": "https://spot.poweremarket.com/uptspot/ma/spot/spottrade/scptp/sr/mp/spottrade/tdSpotRealClearUnitResultInfo/getList",
            "日前均价": "https://spot.poweremarket.com/uptspot/ma/spot/spottrade/scptp/sr/mp/spottrade/baseinfo/TranOver/getWatchDealCountData",
            "实时均价": "https://spot.poweremarket.com/uptspot/ma/spot/spottrade/scptp/sr/mp/spottrade/baseinfo/TranOver/getWatchDealCountData",
            "实时节点电价查询": "https://spot.poweremarket.com/uptspot/ma/spot/spottrade/scptp/sr/mp/spottrade/tdSpotRealClearNodePrice/nodePriceQuery",
            "日前节点电价查询": "https://spot.poweremarket.com/uptspot/ma/spot/spottrade/scptp/sr/mp/spottrade/tdSpotRecentlyNodeInfo/selectGetrecentlyNodeInfo",
            "实时交易结果查询（用电侧）": "https://spot.poweremarket.com/uptspot/ma/spot/spottrade/scptp/sr/mp/spottrade/tdSpotRealResultNodeInfo/getList",
            "日前交易结果查询（用电侧）": "https://spot.poweremarket.com/uptspot/ma/spot/spottrade/scptp/sr/mp/spottrade/tdSpotRecentlyResultUserInfo/getList",

            "实时交易结果查询（用电侧）": "https://spot.poweremarket.com/uptspot/ma/spot/spottrade/scptp/sr/mp/spottrade/tdSpotRealResultNodeInfo/getList",
            "日前交易结果查询（用电侧）": "https://spot.poweremarket.com/uptspot/ma/spot/spottrade/scptp/sr/mp/spottrade/tdSpotRecentlyResultUserInfo/getList",
            "统调负荷2": "https://spot.poweremarket.com/uptspot/ma/spot/spottrade/scptp/sr/mp/spottrade/intePublishVolumeUpCurve/getListPage",
            "发电总出力2": "https://spot.poweremarket.com/uptspot/ma/spot/spottrade/scptp/sr/mp/spottrade/mkGenElecPowerTotalOutput/getObject",
            "非市场化机组总出力2": "https://spot.poweremarket.com/uptspot/ma/spot/spottrade/scptp/sr/mp/spottrade/mkNonMarketUnitAllOutput/getObject",
            "新能源出力2": "https://spot.poweremarket.com/uptspot/ma/spot/spottrade/scptp/sr/mp/spottrade/mkNewEnergyTotalOutputDx/getObject",
            "水电总出力2": "https://spot.poweremarket.com/uptspot/ma/spot/spottrade/scptp/sr/mp/spottrade/mkWaterElecTicTotalOutput/getObject",
            "省间联络线输电情况（getChannelName）2": "https://spot.poweremarket.com/uptspot/ma/spot/spottrade/scptp/sr/mp/spottrade/mkInnerProvLinkTransSitu/getChannelName",
            "省间联络线输电情况2": "https://spot.poweremarket.com/uptspot/ma/spot/spottrade/scptp/sr/mp/spottrade/mkInnerProvLinkTransSitu/getObject"
        }
        
        # 请求头
        self.headers = {
            "user-agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/130.0.0.0 Safari/537.36 QuarkPC/4.1.7.408",
            'Content-Type': 'application/json',
            # 'cookie': 'CAMSID=98511E2F1F6D75978F9573F7853D4EE3'
        }
        
        # 地区代码映射
        self.region_codes = {
            "全区域":"00",
            "广东": "02",
            "广西": "03",
            "云南": "04",
            "贵州": "05",
            "海南": "06"
        }
        
        # 火电开机容量
        self.fire_volume = 17170

    # region 信息披露爬取
    def update_cookie(self, cookie):
        """更新Cookie"""
        self.headers = {**self.headers, 'cookie': cookie}

    def get_tong_diao_fu_he(self, exchange, run_time):
        """获取统调负荷数据"""
        data = {"exchange": exchange, "runTime": run_time}
        response = requests.post(self.url_dict["统调负荷"], headers=self.headers, json=data)
        data = response.json()["data"]["data"]
        return {d["time"]: d["energy"] for d in data}
    
    def get_fei_shi_chang_hua_chu_li(self, exchange, run_time):
        """获取非市场化机组总出力数据"""
        data = {"exchange": exchange, "runTime": run_time}
        response = requests.post(self.url_dict["非市场化机组出力"], headers=self.headers, json=data)
        data = response.json()["data"]["data"]
        return {d["time"]: float(d["energy"]) for d in data}

    def getFeiShiChangDianYuanBuHanXingNengYuanData(self, exchange, runTime):
        data = {
            "areaCode": exchange,
            "runTime": runTime
        }
        response = requests.post(self.url_dict["非市场机组电源不含新能源总出力预测"], headers=self.headers, json=data)
        data = response.json()["data"]["data"]
        return {d["time"]: float(d["tEnergy"]) for d in data}
    
    def get_xin_neng_yuan_zong_chu_li(self, exchange, run_time):
        """获取新能源总出力数据"""
        data = {"exchange": exchange, "runTime": run_time, "dayType": "2", "dataType": "1"}
        response = requests.post(self.url_dict["新能源总出力"], headers=self.headers, json=data)
        data = response.json()["data"]["data"]
        return {d["time"]:float(d["energy01"])for d in data}
    
    def get_zheng_bei_yong(self, exchange, run_time):
        """获取正备用数据"""
        data = {"exchange": exchange, "runTime": run_time, "positiveType": "1"}
        response = requests.post(self.url_dict["正备用"], headers=self.headers, json=data)
        data = response.json()["data"]["data"]["list"][0]["lmplist"]
        return {d["time"]: float(d["value"]) for d in data}
    
    def get_fu_bei_yong(self, exchange, run_time):
        """获取负备用数据"""
        data = {"exchange": exchange, "runTime": run_time, "positiveType": "2"}
        response = requests.post(self.url_dict["负备用"], headers=self.headers, json=data)
        data = response.json()["data"]["data"]["list"][0]["lmplist"]
        return {d["time"]: float(d["value"]) for d in data}
    
    def get_xi_dian_dong_song(self, exchange, run_time):
        """获取西电东送数据"""
        data = {"sectionId": exchange, "operateDate": run_time}
        response = requests.post(self.url_dict["西电东送"], headers=self.headers, json=data)
        data = response.json()["data"]["data"]
        return {d["time"]: float(d["send"]) for d in data}
    
    def get_public_information(self, run_time, region):
        """获取单日公开信息"""
        exchange = self.region_codes.get(region, "05")  # 默认贵州
        
        # 生成标准时间索引 (96个时间点)
        time_index = pd.date_range(f"00:00", f"23:45", freq="15min").strftime("%H:%M")
        date_time_index = pd.date_range(f"{run_time} 00:00", f"{run_time} 23:45", freq="15min").strftime("%Y-%m-%d %H:%M")
        # 生成标准时间索引 (24个时间点)
        W2E_time_index = pd.date_range(f"00:00", f"23:00", freq="1H").strftime("%H:%M")
        W2E_date_time_index = pd.date_range(f"{run_time} 00:00", f"{run_time} 23:00", freq="1H").strftime("%Y-%m-%d %H:%M")
        
        # 收集所有数据源
        try:
            data_sources = {
                "统调负荷": self.get_tong_diao_fu_he(exchange, run_time),
                # "非市场化机组总出力": self.get_fei_shi_chang_hua_chu_li(exchange, run_time),
                "非市场机组电源不含新能源总出力预测":self.getFeiShiChangDianYuanBuHanXingNengYuanData(exchange, run_time),
                "新能源总出力（周）": self.get_xin_neng_yuan_zong_chu_li(exchange, run_time),
                "正备用": self.get_zheng_bei_yong(exchange, run_time),
                "负备用": self.get_fu_bei_yong(exchange, run_time),
                "西电东送": self.get_xi_dian_dong_song(exchange, run_time)
            }
        except Exception as e:
            return None,None, f"获取数据时出错: {str(e)}"
        
        # 创建空DataFrame（带标准时间索引）
        df = pd.DataFrame(index=time_index)
        
        # 逐个处理数据源并添加到DataFrame
        for name, data_dict in data_sources.items():
            # 转换为数值型Series
            s = pd.Series(data_dict).astype(float)
            # 按标准索引对齐（缺失值自动为NaN）
            s_aligned = s.reindex(time_index)
            # 添加到DataFrame
            df[name] = s_aligned
        
        # 数据处理
        df['西电东送'] = df['西电东送'].ffill()
        df['火电竞价空间'] = (
            df['统调负荷']
            -df['非市场机组电源不含新能源总出力预测']
            -df['新能源总出力（周）']
            -df['西电东送']
        )
        df['负荷率'] = ((df['火电竞价空间']+df['西电东送'])/ self.fire_volume).apply(lambda x: f"{x:.2%}")

        df = df[['统调负荷','新能源总出力（周）', '非市场机组电源不含新能源总出力预测', '正备用', '负备用', '火电竞价空间', '负荷率','西电东送']]
        df.index = date_time_index

        # 创建西电东送专用DataFrame（小时频率）
        powerData_WestToEast_df = pd.DataFrame({
            '西电东送': pd.Series(data_sources["西电东送"]).reindex(W2E_time_index)
        })
        powerData_WestToEast_df.index = W2E_date_time_index
        
        return df, powerData_WestToEast_df, None

    def get_public_information_by_date_range(self, start_date, end_date, region):
        """根据日期范围获取日前披露数据"""
        start_dt = datetime.strptime(start_date, "%Y-%m-%d")
        end_dt = datetime.strptime(end_date, "%Y-%m-%d")

        # 初始化一个空的DataFrame
        result_df = pd.DataFrame()
        powerData_W2E_result_df = pd.DataFrame()
        errors = []

        # 遍历每一天
        current_date = start_dt
        while current_date <= end_dt:
            date_str = current_date.strftime("%Y%m%d")
            daily_df, powerData_W2E_df, error = self.get_public_information(date_str, region)

            if daily_df is not None:
                result_df = pd.concat([result_df, daily_df], axis=0)
                powerData_W2E_result_df = pd.concat([powerData_W2E_result_df, powerData_W2E_df], axis=0)
                yield f"已完成 {current_date.strftime('%Y-%m-%d')} 披露信息获取", None, False
            else:
                errors.append(f"{current_date.strftime('%Y-%m-%d')}: {error}")
                yield f"获取 {current_date.strftime('%Y-%m-%d')} 数据失败: {error}", None, False

            # 移动到下一天
            current_date += timedelta(days=1)

        if not result_df.empty:
            yield result_df,powerData_W2E_result_df,True
        else:
            yield "没有获取到任何有效数据",powerData_W2E_result_df, True
            yield "\n".join(errors),powerData_W2E_result_df, True

    # endregion

    #region 实时信息披露爬取
    def update_cookie(self, cookie):
        """更新Cookie"""
        self.headers = {**self.headers, 'cookie': cookie}

    def get_tdfh(self, exchange, run_time):
        data = {"exchange": exchange, "runTime": run_time}
        response = requests.post(self.url_dict["统调负荷2"], headers=self.headers, json=data)
        data = response.json()["data"]["data"]["list"][0]["activepowerList"]
        return {d["time"]: d["value"] for d in data}

    def get_fa_dian_zong_chu_li(self, exchange, run_time):
        data = {"areaNo": exchange, "runTime": run_time}
        response = requests.post(self.url_dict["发电总出力2"], headers=self.headers, json=data)
        data = response.json()["data"]["data"]
        return {d["time"]: d["tEnergy"] for d in data}

    def get_fei_shi_chang_hua_ji_zu_zong_chu_li(self, exchange, run_time):
        data = {"areaCode": exchange, "runTime": run_time}
        response = requests.post(self.url_dict["非市场化机组总出力2"], headers=self.headers, json=data)
        data = response.json()["data"]["data"]
        return {d["time"]: d["tEnergy"] for d in data}

    def get_xin_neng_yuan_zong_chu_li_qu_xian(self, exchange, run_time):
        data = {"areaNo": exchange, "runTime": run_time}
        response = requests.post(self.url_dict["新能源出力2"], headers=self.headers, json=data)
        data = response.json()["data"]["data"]
        return {d["time"]: d["tEnergy"] for d in data}

    def get_shui_dian_zong_chu_li(self, exchange, run_time):
        data = {"areaNo": exchange, "runTime": run_time}
        response = requests.post(self.url_dict["水电总出力2"], headers=self.headers, json=data)
        data = response.json()["data"]["data"]
        return {d["time"]: d["tEnergy"] for d in data}

    def get_sheng_jian(self, run_time):
        data = {"runTime": run_time}
        response = requests.post(self.url_dict["省间联络线输电情况（getChannelName）2"], headers=self.headers, json=data)
        data = response.json()["data"]["data"]
        target_mk_id = None
        for item in data:
            if item["name"] == "贵州总送出":
                target_mk_id = item["mkId"]
        mkid = target_mk_id
        data = {"mkId": mkid, "runTime": run_time}
        response = requests.post(self.url_dict["省间联络线输电情况2"], headers=self.headers, json=data)
        data = response.json()["data"]["data"]
        return {d["time"]: d["energy"] for d in data}

    def get_real_time_public_information(self, run_time, region):
        """获取单日公开信息"""
        exchange = self.region_codes.get(region, "05")  # 默认贵州

        # 生成标准时间索引 (96个时间点)
        time_index = pd.date_range(f"00:00", f"23:45", freq="15min").strftime("%H:%M")
        date_time_index = pd.date_range(f"{run_time} 00:00", f"{run_time} 23:45", freq="15min").strftime("%Y-%m-%d %H:%M")

        # 收集所有数据源
        try:
            data_sources = {
                "统调负荷": self.get_tdfh(exchange, run_time),
                "发电总出力": self.get_fa_dian_zong_chu_li(exchange, run_time),
                "非市场化机组总出力": self.get_fei_shi_chang_hua_ji_zu_zong_chu_li(exchange, run_time),
                "新能源出力": self.get_xin_neng_yuan_zong_chu_li_qu_xian(exchange, run_time),
                "水电总出力": self.get_shui_dian_zong_chu_li(exchange, run_time),
                "省间联络线输电情况": self.get_sheng_jian(run_time)
            }
        except Exception as e:
            return None, f"获取数据时出错: {str(e)}"
        # 创建空DataFrame（带标准时间索引）
        df = pd.DataFrame(index=time_index)

        # 逐个处理数据源并添加到DataFrame
        for name, data_dict in data_sources.items():
            # 转换为数值型Series
            s = pd.Series(data_dict).astype(float)
            # 按标准索引对齐（缺失值自动为NaN）
            s_aligned = s.reindex(time_index)
            # 添加到DataFrame
            df[name] = s_aligned

        # 数据处理
        df = df[['统调负荷', '发电总出力', '非市场化机组总出力', '新能源出力', '水电总出力', '省间联络线输电情况']]
        df.index = date_time_index

        return df, None



    def get_real_time_public_information_by_date_range(self, run_time, region):

        start_dt = datetime.strptime(run_time, "%Y-%m-%d")
        end_dt = datetime.strptime(run_time, "%Y-%m-%d")
            # 初始化一个空的DataFrame
        result_df = pd.DataFrame()
        errors = []

            # 遍历每一天
        current_date = start_dt
        while current_date <= end_dt:
            date_str = current_date.strftime("%Y%m%d")
            daily_df, error = self.get_real_time_public_information(date_str, region)

            if daily_df is not None:
                result_df = pd.concat([result_df, daily_df], axis=0)
                yield f"已完成 {current_date.strftime('%Y-%m-%d')} 披露信息获取",  False
            else:
                errors.append(f"{current_date.strftime('%Y-%m-%d')}: {error}")
                yield f"获取 {current_date.strftime('%Y-%m-%d')} 数据失败: {error}",  False
                #移动到下一天
            current_date += timedelta(days=1)

        if not result_df.empty:
            yield result_df,  True
        else:
            yield "没有获取到任何有效数据",  True
            yield "\n".join(errors),  True

    #endregion

    # region 日前/实时电量电价爬取
    def get_recently_data(self, unit_id, run_time):
        """获取日前交易结果（发电侧）"""
        data = {
            "operatingDate": run_time,
            "unitId": unit_id
        }
        response = requests.post(self.url_dict["日前交易结果查询（发电侧）"], headers=self.headers, json=data)
        df = pd.DataFrame()
        try:
            data = response.json()["data"]["data"][0]["infoList"]

            # 提取所需数据
            formatted_data = []
            for item in data:
                formatted_data.append({
                    '时间': item["time"],
                    '日前电量': item['timeValue'],
                    '日前电价': item['hourPrice']
                })

            # 创建DataFrame
            df = pd.DataFrame(formatted_data)
            df.set_index('时间', inplace=True)
            df.sort_index(inplace=True)
        finally:
            return df

    def get_real_time_data(self, unit_id, run_time):
        """获取实时交易结果（发电侧）"""
        data = {
            "operatingDate": run_time,
            "unitId": unit_id
        }
        response = requests.post(self.url_dict["实时交易结果查询（发电侧）"], headers=self.headers, json=data)
        df = pd.DataFrame()
        try:
            data = response.json()["data"]["data"][0]["infoList"]

            # 提取所需数据
            formatted_data = []
            for item in data:
                formatted_data.append({
                    '时间': item["time"],
                    '实时电量': item['timeValue'],
                    '实时电价': item['hourPrice']
                })

            # 创建DataFrame
            df = pd.DataFrame(formatted_data)
            df.set_index('时间', inplace=True)
            df.sort_index(inplace=True)
        finally:
            return df

    def get_area_deal_data(self, exchange, time):
        """获取区域日前/实时均价"""
        area_deal_dict = {}

        # 日前均价
        data = {"dateId": "0", "exchange": exchange, "operateDate": time}
        response = requests.post(self.url_dict["日前均价"], headers=self.headers, json=data)
        try:
            data = response.json()["data"][0]
            area_deal_dict["发电侧_日前平均电价"] = data["powerDealAvg"]
            area_deal_dict["用电侧_日前平均电价"] = data["userDealAvg"]
        except Exception as e:
            area_deal_dict["发电侧_日前平均电价"] = None
            area_deal_dict["用电侧_日前平均电价"] = None

        # 实时均价
        data = {"dateId": "1", "exchange": exchange, "operateDate": time}
        response = requests.post(self.url_dict["实时均价"], headers=self.headers, json=data)
        try:
            data = response.json()["data"][0]
            area_deal_dict["发电侧_实时平均电价"] = data["powerDealAvg"]
            area_deal_dict["用电侧_实时平均电价"] = data["userDealAvg"]
        except Exception as e:
            area_deal_dict["发电侧_实时平均电价"] = None
            area_deal_dict["用电侧_实时平均电价"] = None


        return area_deal_dict

    def get_area_deal_time_data(self, run_time):
        """获取所有区域均价数据"""
        area_deal_dict = {}

        for region, code in self.region_codes.items():
            area_deal_dict[region] = self.get_area_deal_data(code, run_time)

        return pd.DataFrame.from_dict(area_deal_dict, orient='index').astype(float)

    def get_station_data(self, station_name, unit_id, run_time):
        """获取场站的日前和实时数据"""
        time_index = pd.date_range(f"00:00", f"23:00", freq="1H").strftime("%H:%M")  # 不带日期的索引
        # 初始化空DataFrame
        recently_df = pd.DataFrame(columns=['日前电量', '日前电价'],index=time_index)
        realtime_df = pd.DataFrame(columns=['实时电量', '实时电价'],index=time_index)
        area_df = pd.DataFrame()
        error_msgs = []

        # 获取日前数据
        try:
            df = self.get_recently_data(unit_id, run_time)
            if not df.empty:
                recently_df.update(df)
            else:
                error_msgs.append(f"错误: {station_name} {run_time} 日前数据为空")
        except Exception as e:
            error_msgs.append(f"错误: {station_name} {run_time} 日前数据获取失败({str(e)})")

        # 获取实时数据
        try:
            df = self.get_real_time_data(unit_id, run_time)
            if not df.empty:
                realtime_df.update(df)
            else:
                error_msgs.append(f"错误: {station_name} {run_time} 实时数据为空")
        except Exception as e:
            error_msgs.append(f"错误: {station_name} {run_time} 实时数据获取失败({str(e)})")

        # 获取区域均价数据
        try:
            area_df = self.get_area_deal_time_data(run_time)
            if area_df.empty:
                error_msgs.append(f"警告: {run_time} 区域均价数据为空")
        except Exception as e:
            error_msgs.append(f"警告: {run_time} 区域均价数据获取失败({str(e)})")

        # # 合并数据
        # merged_df = pd.concat([recently_df, realtime_df], axis=1)
        # 如果有错误消息，合并为一条消息
        error_msg = "\n".join(error_msgs) if error_msgs else None

        merged_df = pd.merge(
            recently_df,
            realtime_df,
            left_index=True,
            right_index=True,
            how='outer'
        )
        return merged_df, area_df, error_msg if error_msgs else None
    # endregion

    # region 节点日前/实时电价爬取
    def getRecentlyPriceByDate(self, date, node_ids, nodeName):
        '''日前电价爬取'''
        json = {
            "exchange": "05"
            , "nodeId": node_ids[nodeName]
            , "operatingDate": date
            , "unitName": nodeName
        }

        response = requests.request("POST", self.url_dict["日前节点电价查询"], headers=self.headers, json=json)
        try:
            data = response.json()["data"]["data"]["time"]
            value = {d["time"]: float(d["timeValue"]) for d in data}
            time.sleep(2)
            return value
        except:
            return []

    def getRealTimePriceByDate(self, date, node_ids, nodeName):
        '''实施电价爬取'''
        json = {
            "areaCode": "GuiZ"
            , "exchange": "05"
            , "nodeId": node_ids[nodeName]
            , "operatingDate": date
        }

        response = requests.request("POST", self.url_dict["实时节点电价查询"], headers=self.headers, json=json)
        try:
            data = response.json()["data"]["data"]

            value = {d["time"]: float(d["price"]) for d in data}
            time.sleep(2)
            return value
        except:
            return []

    def collect_single_day_prices(self, date_str,node_ids,progress_callback=None):
        """
        收集单日所有节点的日前电价和实时电价
        :param date_str: 日期字符串，例如 '2025-08-15'
        :return: DataFrame，index=时间，列=节点+电价类型
        """
        # 1. 生成标准时间索引 (96个时间点)
        time_index = pd.date_range("00:00", "23:45", freq="15min").strftime("%H:%M")

        # 2. 收集所有数据源
        progress_value = 0
        data_sources = {}
        for name, node_id in node_ids.items():
            #爬取日前电价
            data_sources[f"{name[0:2]}日前电价"] = self.getRecentlyPriceByDate(date_str,node_ids, name)
            progress_value += 1
            progress_callback(progress_value,f"已获取{name[0:2]}日前电价（{progress_value}/{2*len(node_ids)}）")

            #爬取实时电价
            data_sources[f"{name[0:2]}实时电价"] = self.getRealTimePriceByDate(date_str,node_ids, name)
            progress_value += 1
            progress_callback(progress_value,f"已获取{name[0:2]}实时电价（{progress_value}/{2*len(node_ids)}）")

        # 3. 创建空 DataFrame
        df_15min = pd.DataFrame(index=time_index)

        # 4. 对齐并填充
        for name, data_dict in data_sources.items():
            s = pd.Series(data_dict).astype(float)
            s_aligned = s.reindex(time_index)
            df_15min[name] = s_aligned

        df_15min.index = pd.to_datetime(df_15min.index, format="%H:%M")
        return df_15min

    def collect_multi_days_prices(self, start_date, end_date,node_ids,progress_callback=None):
        """
        收集多日所有节点的日前和实时电价
        :param start_date: datetime 对象
        :param end_date: datetime 对象
        :return: DataFrame，index=日期时间
        """
        all_days = []
        current_date = start_date

        while current_date <= end_date:
            date_str = current_date.strftime("%Y-%m-%d")
            df_day = self.collect_single_day_prices(date_str,node_ids,progress_callback=progress_callback)
            if progress_callback:
                progress_callback(0,f"已完成{date_str}节点电价爬取")

            # 为每行加上完整日期时间索引
            full_datetime_index = [
                datetime.combine(current_date.date(), t.time()) for t in df_day.index
            ]
            df_day.index = pd.to_datetime(full_datetime_index)

            all_days.append(df_day)
            current_date += timedelta(days=1)

        # 合并
        df_all = pd.concat(all_days)
        return df_all
    # endregion