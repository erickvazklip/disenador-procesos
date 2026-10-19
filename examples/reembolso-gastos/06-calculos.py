# Cálculos de 06-analisis-cuantitativo.md y 07-rediseno.md. Ejecutar: python3 06-calculos.py
# Todos los parámetros son [SUPUESTO] salvo 10 min de captura, 15 % incompletos, 2 días de alta y 60 informes/semana (IN-03).
# Flow analysis as-is / to-be. Unidades: días hábiles (8 h) y minutos.
H=8*60
def asis(boss_wait=4.0, cxp_wait=3.0, prep_first=3.0, prep_re=1.0, p_jefe=0.10, p_cxp=0.15,
         p_plazo=0.03, p_exc=0.20, p_noaut=0.30, p_prov=0.10, df_wait=2.0, ti_days=2.0, corrida_wait=5.0, banco=1.0):
    # tiempos de proceso (min)
    t_prep, t_env, t_rev, t_dev, t_apr, t_cap, t_ver, t_devc = 30,2,5,3,2,10,5,3
    t_sol, t_df, t_aj, t_vcta, t_salta, t_alta, t_pag = 3,10,5,2,3,15,2
    ps = (1-p_jefe)*(1-p_cxp)          # prob. de pasar ambos filtros en un intento
    n = 1/ps                           # intentos esperados
    # CT de un intento (sin la prep), prep primera vs re
    att_ct = boss_wait + (1-p_jefe)*cxp_wait
    loop_ct = prep_first + (n-1)*prep_re + n*att_ct
    att_pt = t_env + t_rev + p_jefe*t_dev + (1-p_jefe)*(t_apr + t_cap + t_ver + p_cxp*t_devc)
    loop_pt = n*(t_prep + att_pt)
    q = 1-p_plazo  # siguen tras plazo
    post_ct = q*(p_exc*(df_wait) + p_prov*ti_days + corrida_wait + banco)
    post_pt = q*(p_exc*(t_sol+t_df+p_noaut*t_aj) + t_vcta + p_prov*(t_salta+t_alta) + t_pag)
    CT = loop_ct + post_ct
    TCT = loop_pt + post_pt
    # carga por rol (min/caso)
    ul = {
     'Empleado': n*(t_prep+t_env),
     'Jefe': n*(t_rev + p_jefe*t_dev + (1-p_jefe)*t_apr),
     'CxP': n*(1-p_jefe)*(t_cap+t_ver+p_cxp*t_devc) + q*(p_exc*(t_sol+p_noaut*t_aj)+t_vcta+p_prov*t_salta+t_pag),
     'DF': q*p_exc*t_df, 'TI': q*p_prov*t_alta}
    return dict(n=n, loop_ct=loop_ct, CT=CT, TCT=TCT, CTE=TCT/(CT*H), ul=ul)
rate = {'Empleado':250,'Jefe':450,'CxP':200,'DF':1200,'TI':250}  # MXN/h [SUPUESTO]
def cost(ul): return sum(ul[k]/60*rate[k] for k in ul)
a = asis()
print('AS-IS', {k:(round(v,3) if not isinstance(v,dict) else {kk:round(vv,2) for kk,vv in v.items()}) for k,v in a.items()})
print('coste/caso', round(cost(a['ul']),1), 'anual (60x48)', round(cost(a['ul'])*60*48))
# capacidad CxP
lam = 12  # informes/día
for hrs in (4,3,3.5,5):
    mu = hrs*60/a['ul']['CxP']; rho=lam/mu
    Lq = rho**2/(1-rho) if rho<1 else float('inf'); Wq = Lq/lam if rho<1 else float('inf')
    print(f'CxP {hrs} h/día: mu={mu:.2f}/día rho={rho:.2f} Lq={Lq:.2f} Wq={Wq:.2f} d')
print('WIP Little (CT en días hábiles)', round(lam*a['CT'],1))
# sensibilidad
for name,kw in [('jefe espera 2.5',dict(boss_wait=2.5)),('jefe espera 6',dict(boss_wait=6)),('cxp espera 1',dict(cxp_wait=1)),('cxp 5',dict(cxp_wait=5)),
                ('p_jefe 0.05',dict(p_jefe=0.05)),('p_jefe 0.20',dict(p_jefe=0.20)),('corrida semanal',dict(corrida_wait=2.5)),('prep_first 1',dict(prep_first=1)),('prep_first 5',dict(prep_first=5))]:
    r=asis(**kw); print('sens',name, round(r['CT'],2))
# contribuciones de espera (días por caso) para Pareto
n=a['n']
contrib = {
 'I1 Revisión del jefe en lote semanal': n*4.0,
 'I2 Rework por informes incompletos (intentos extra)': (n-1)*(1.0) + (n-1)*(4.0+0.9*3.0),
 'I3 Cola y captura manual en CxP': n*0.9*3.0,
 'I4 Corrida quincenal': 0.97*5.0,
 'I5 Autorización DF de excedentes': 0.97*0.2*2.0,
 'I6 Alta reactiva de proveedor': 0.97*0.1*2.0,
}
print({k:round(v,2) for k,v in contrib.items()})
# to-be
def tobe(p_inc=0.03, p_auto=0.35, p_corr=0.03, p_rech=0.01, p_exc=0.20, boss_wait=1.0, df_wait=1.0, corrida_wait=2.5, banco=1.0, prep=1.0, p_aud=0.10+0.2*0.9):
    t_reg, t_apr, t_df, t_aud = 25, 3, 10, 10
    # bucle: incompleto (portal) y corrección del jefe
    r = p_inc + (1-p_inc)*(1-p_auto)*p_corr
    n = 1/(1-r)
    att_ct = (1-p_inc)*(1-p_auto)*boss_wait
    loop_ct = prep + n*att_ct + (n-1)*0.25
    q = 1 - 0.01  # fuera de plazo marginal
    post_ct = q*((1-p_auto)*p_exc*df_wait + corrida_wait + banco)
    CT = loop_ct + post_ct
    ul = {'Empleado': n*t_reg, 'Jefe': n*(1-p_inc)*(1-p_auto)*t_apr, 'DF': q*(1-p_auto)*p_exc*t_df, 'CxP': q*min(p_aud,1)*t_aud, 'TI':0}
    TCT = sum(ul.values()) + 2
    return dict(n=n, CT=CT, TCT=TCT, CTE=TCT/(CT*H), ul=ul)
b=tobe(); print('TO-BE', {k:(round(v,3) if not isinstance(v,dict) else {kk:round(vv,2) for kk,vv in v.items()}) for k,v in b.items()})
print('coste/caso', round(cost(b['ul']),1), 'anual', round(cost(b['ul'])*60*48))
for name,kw in [('jefe 2d',dict(boss_wait=2)),('auto 0.2',dict(p_auto=0.2)),('corrida quincenal',dict(corrida_wait=5)),('prep 3',dict(prep=3))]:
    print('sens tobe',name, round(tobe(**kw)['CT'],2))
# escenario quick wins S1 (sin TI): jefe 2 veces/semana (1.25 d), corrida semanal, checklist p_jefe .05 p_cxp .08
s1=asis(boss_wait=1.5, p_jefe=0.05, p_cxp=0.08, corrida_wait=2.5); print('S1 CT', round(s1['CT'],2), 'coste', round(cost(s1['ul']),1))
