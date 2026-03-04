// LoveSpace C++ Core — lovespace_core.cpp
// Сборка Linux:   g++ -O2 -std=c++14 -shared -fPIC -o lovespace_core.so lovespace_core.cpp
// Сборка Windows: g++ -O2 -std=c++14 -shared -o lovespace_core.dll lovespace_core.cpp

#include <cstring>
#include <cstdlib>
#include <cstdio>
#include <cmath>
#include <algorithm>

#pragma pack(push, 1)
struct TimeSlot       { int day, start_min, end_min; };
struct ScoreEntry     { int user_id, points; };
struct CategoryStats  { char name[64]; double amount, percent; };
struct DistribResult  { int assign[512]; int score0, score1, diff; };
#pragma pack(pop)

// ── Слить пересекающиеся интервалы ──────────────────────────────────────────
static void merge_intervals(int* s, int* e, int& n) {
    for (int i=0;i<n-1;i++) for (int j=i+1;j<n;j++) if(s[i]>s[j]){std::swap(s[i],s[j]);std::swap(e[i],e[j]);}
    int ms[128],me[128],mc=0;
    for(int i=0;i<n;i++){
        if(mc==0||s[i]>me[mc-1]){ms[mc]=s[i];me[mc++]=e[i];}
        else me[mc-1]=std::max(me[mc-1],e[i]);
    }
    for(int i=0;i<mc;i++){s[i]=ms[i];e[i]=me[i];} n=mc;
}

extern "C" {

// Найти совместное свободное время (08:00–22:00, блоки >= 60 мин)
int find_free_time(
    const TimeSlot* a, int ac,
    const TimeSlot* b, int bc,
    TimeSlot* out, int max_out
) {
    const int DS=8*60, DE=22*60, MB=60;
    int found=0;
    for(int day=0;day<7&&found<max_out;day++){
        int bs[128],be[128],tc=0;
        for(int i=0;i<ac&&tc<127;i++) if(a[i].day==day){bs[tc]=a[i].start_min;be[tc++]=a[i].end_min;}
        for(int i=0;i<bc&&tc<127;i++) if(b[i].day==day){bs[tc]=b[i].start_min;be[tc++]=b[i].end_min;}
        merge_intervals(bs,be,tc);
        int cur=DS;
        for(int i=0;i<=tc&&found<max_out;i++){
            int seg=(i<tc)?std::min(bs[i],DE):DE;
            if(seg>cur&&seg-cur>=MB){out[found++]={day,cur,seg};}
            if(i<tc) cur=std::max(cur,be[i]);
        }
    }
    return found;
}

// Подсчёт очков участников
int calc_weekly_scores(const int* u,const int* p,int n,ScoreEntry* out,int mx){
    int ids[256],sc[256],uc=0;
    for(int i=0;i<n;i++){
        int fi=-1; for(int j=0;j<uc;j++) if(ids[j]==u[i]){fi=j;break;}
        if(fi<0&&uc<256){ids[uc]=u[i];sc[uc]=0;fi=uc++;}
        if(fi>=0) sc[fi]+=p[i];
    }
    int r=std::min(uc,mx);
    for(int i=0;i<r;i++){out[i].user_id=ids[i];out[i].points=sc[i];}
    for(int i=0;i<r-1;i++) for(int j=i+1;j<r;j++) if(out[i].points<out[j].points) std::swap(out[i],out[j]);
    return r;
}

// Равномерное распределение задач (жадный)
int distribute_tasks(const int* pts,int n,DistribResult* res){
    if(n>512) n=512;
    int sc[2]={0,0};
    for(int i=0;i<n;i++){int w=(sc[0]<=sc[1])?0:1;res->assign[i]=w;sc[w]+=pts[i];}
    res->score0=sc[0]; res->score1=sc[1]; res->diff=abs(sc[0]-sc[1]);
    return res->diff;
}

// Процентное соотношение категорий расходов
int analyze_categories(const double* a,const char** names,int n,CategoryStats* out){
    double tot=0; for(int i=0;i<n;i++) tot+=a[i]; if(tot<=0) tot=1;
    for(int i=0;i<n;i++){strncpy(out[i].name,names[i],63);out[i].name[63]=0;out[i].amount=a[i];out[i].percent=a[i]/tot*100.0;}
    for(int i=0;i<n-1;i++) for(int j=i+1;j<n;j++) if(out[i].amount<out[j].amount) std::swap(out[i],out[j]);
    return n;
}

// Серия дней с отмеченным настроением
int mood_streak(const char** dates, int n){
    if(n==0) return 0;
    auto pd=[](const char*s){int y,m,d;sscanf(s,"%d-%d-%d",&y,&m,&d);return y*365+m*30+d;};
    int streak=1,prev=pd(dates[0]);
    for(int i=1;i<n;i++){int c=pd(dates[i]);if(prev-c==1){streak++;prev=c;}else break;}
    return streak;
}

// Хэш инвайт-кода FNV-1a
unsigned int hash_invite_code(const char* code){
    unsigned int h=2166136261u;
    while(*code){h^=(unsigned char)*code++;h*=16777619u;}
    return h;
}

const char* lovespace_version(){ return "LoveSpace C++ Core v1.0"; }

} // extern "C"
