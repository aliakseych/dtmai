"""Idempotently publish the official exam-hall reference sheets ("Formulalar") per subject.

The sheets are transcribed from the handouts given at the real exam
(`../dtmai-data/formulas/Imtihonda beriladigan formulalar.pdf`, 4 pages: mathematics, physics,
physical constants and substance tables; `kimyo formula va jadval.pdf`: chemistry formulas, periodic
table, solubility table). Goes through the admin HTTP API
(PUT /v1/admin/catalog/subjects/{id}/reference), so re-running replaces the previous content instead of
duplicating it. Subjects are matched by `code` (math, physics, chemistry); missing subjects are skipped.
Locales seeded: uz-Latn and ru (uz-Cyrl/en fall back to uz-Latn/ru).

Text segments written as `⟦uz||ru⟧` are resolved per locale; everything else is language-neutral.

Usage: API_URL=http://localhost:8000 ADMIN_EMAIL=... ADMIN_PASSWORD=... \
       uv run python scripts/seed_reference_sheets.py
"""

import asyncio
import os
import re

import httpx

API = os.environ.get("API_URL", "http://localhost:8000")
EMAIL = os.environ.get("ADMIN_EMAIL", "admin@dtm-ai.uz")
PASSWORD = os.environ.get("ADMIN_PASSWORD", "AdminPass123!")

SOURCE = {
    "uz-Latn": "Imtihonda beriladigan rasmiy formulalar varaqasi",
    "ru": "Официальный справочный лист, выдаваемый на экзамене",
}

_SEG = re.compile(r"⟦(.*?)\|\|(.*?)⟧", re.S)


def render(src: str, loc: str) -> str:
    idx = 1 if loc == "ru" else 0
    return _SEG.sub(lambda m: m.group(idx + 1), src).strip()


MATH = r"""
## ⟦Tenglamalar||Уравнения⟧
- $ax^2+bx+c=0$; $\; x_{1,2}=\dfrac{-b\pm\sqrt{b^2-4ac}}{2a}$; $\; x_1+x_2=-\dfrac{b}{a}$, $\; x_1x_2=\dfrac{c}{a}$
- $\lvert f(x)\rvert+\lvert g(x)\rvert=\lvert f(x)+g(x)\rvert \Rightarrow f(x)\cdot g(x)\ge 0$
- $\dfrac{Ax}{ax^2\pm bx+c}\pm\dfrac{Bx}{ax^2\pm dx+c}=k \Rightarrow \dfrac{A}{ax+\frac{c}{x}\pm b}\pm\dfrac{B}{ax+\frac{c}{x}\pm d}=k$
- $(ax^2\pm bx+c)(ax^2\pm dx+c)=Ax^2 \Rightarrow \left(ax+\dfrac{c}{x}\pm b\right)\left(ax+\dfrac{c}{x}\pm d\right)=A$
- $ax+\dfrac{c}{x}=z$ ⟦o‘zgaruvchi kiritib yechiladi||— решается с помощью замены⟧
- $(x-a)(x-b)(x-c)(x-d)=A$, $a+b=c+d$ ⟦bo‘lsa, $t=x^2-(a+b)x$ o‘zgaruvchi kiritib yechiladi||: решается заменой $t=x^2-(a+b)x$⟧

## ⟦Qisqa ko‘paytirish formulalari||Формулы сокращённого умножения⟧
- $a^2-b^2=(a-b)(a+b)$
- $(a\pm b)^2=a^2\pm 2ab+b^2$
- $(a\pm b)^3=a^3\pm 3a^2b+3ab^2\pm b^3$
- $a^3\pm b^3=(a\pm b)(a^2\mp ab+b^2)$
- $a^n-b^n=(a-b)(a^{n-1}+a^{n-2}b+\ldots+ab^{n-2}+b^{n-1})$
- $a^{2n}\pm b^{2n}=(a\pm b)(a^{2n-1}\mp a^{2n-2}b+\ldots+ab^{2n-2}\mp b^{2n-1})$
- $a^{2n+1}\pm b^{2n+1}=(a\pm b)(a^{2n}\mp a^{2n-1}b+\ldots\mp ab^{2n-1}+b^{2n})$
- $(a+b)^n=a^n+na^{n-1}b+\dfrac{n(n-1)}{2!}a^{n-2}b^2+\ldots+\dfrac{n(n-1)(n-2)\cdots(n-(k-1))}{k!}a^{n-k}b^k+\ldots+nab^{n-1}+b^n$

## ⟦Arifmetik progressiya||Арифметическая прогрессия⟧
- $a_n=a_{n-1}+d=a_1+(n-1)d$; $\; a_n=\dfrac{a_{n-k}+a_{n+k}}{2}$, $\; 1\le k\le n-1$
- $S_n=\dfrac{a_1+a_n}{2}\cdot n=\dfrac{2a_1+d(n-1)}{2}\cdot n$

## ⟦Geometrik progressiya||Геометрическая прогрессия⟧
- $b_n=b_1q^{n-1}$; $\; b_n^2=b_{n-m}\cdot b_{n+m}$, $\; 1\le m\le n-1$
- $S_n=\dfrac{b_1(1-q^n)}{1-q}$, $\lvert q\rvert>1$; $\quad S=\dfrac{b_1}{1-q}$, $\lvert q\rvert<1$

## ⟦Logarifmning xossalari||Свойства логарифмов⟧
- $\log_a 1=0$; $\; \log_a(x_1x_2)=\log_a\lvert x_1\rvert+\log_a\lvert x_2\rvert$
- $\log_a\dfrac{x_1}{x_2}=\log_a\lvert x_1\rvert-\log_a\lvert x_2\rvert$; $\; \log_{a^q}x^p=\dfrac{p}{q}\log_a x$
- $\log_a b=\dfrac{\log_c b}{\log_c a}$; $\; \log_a b=\dfrac{1}{\log_b a}$; $\; \lg 10^n=n$; $\; \ln e^n=n$

## ⟦Daraja va ildiz||Степени и корни⟧
- $a^m\cdot a^n=a^{m+n}$; $\; a^m:a^n=a^{m-n}$; $\; (a^m)^n=a^{mn}$; $\; (a\cdot b)^n=a^n\cdot b^n$
- $\left(\dfrac{a}{b}\right)^n=\dfrac{a^n}{b^n}$; $\; a^{-n}=\dfrac{1}{a^n}$; $\; \left(\dfrac{a}{b}\right)^{-n}=\left(\dfrac{b}{a}\right)^n$; $\; (-a)^{2n}=a^{2n}$; $\; (-a)^{2n+1}=-a^{2n+1}$; $\; a\ne0,\ b\ne0,\ n,m\in N$
- $\sqrt[n]{a^k}=a^{k/n}$; $\; \sqrt[n]{a^k\cdot b^m}=\sqrt[n]{a^k}\cdot\sqrt[n]{b^m}$; $\; \sqrt[n]{\dfrac{a^k}{b^m}}=\dfrac{\sqrt[n]{a^k}}{\sqrt[n]{b^m}}$, $b\ne0$
- $\left(\sqrt[n]{a^m}\right)^k=\sqrt[n]{a^{mk}}$; $\; \sqrt[n]{a^{n+k}}=a\sqrt[n]{a^k}$; $\; a^{-\frac{m}{n}}=\dfrac{1}{\sqrt[n]{a^m}}$, $a\ne0$
- $\sqrt[m]{\sqrt[n]{a}}=\sqrt[mn]{a}$; $\; \sqrt[n]{a^k}\cdot\sqrt[p]{b^m}=\sqrt[np]{a^{kp}\cdot b^{mn}}$
- $\sqrt[n]{a^n}=\begin{cases}\lvert a\rvert, & n=2k,\ k\in N\\ a, & n=2k+1,\ k\in N\end{cases}$
- $\sqrt[2n]{(a-b)^{2n}}=\begin{cases}a-b, & a\ge b\\ b-a, & a<b\end{cases}$

## ⟦Urinma va normal tenglamasi||Уравнение касательной и нормали⟧
- $y=f(x_0)+f'(x_0)(x-x_0)$; $\; y=f(x_0)-\dfrac{1}{f'(x_0)}(x-x_0)$

## ⟦Hosilaga doir formulalar||Таблица производных⟧
- $(x^n)'=nx^{n-1}$; $\; (a^x)'=a^x\ln a$; $\; (e^x)'=e^x$; $\; (\log_a x)'=\dfrac{1}{x\ln a}$; $\; (\ln x)'=\dfrac{1}{x}$
- $(\sin x)'=\cos x$; $\; (\cos x)'=-\sin x$; $\; (\operatorname{tg}x)'=\dfrac{1}{\cos^2x}$; $\; (\operatorname{ctg}x)'=-\dfrac{1}{\sin^2x}$

## ⟦Hosilaning xossalari||Свойства производных⟧
- $(u(x)\pm v(x))'=u'(x)\pm v'(x)$; $\; (k\cdot u(x))'=k\cdot u'(x)$, $k=const$
- $(u(x)\cdot v(x))'=u'(x)\cdot v(x)+u(x)\cdot v'(x)$
- $\left(\dfrac{u(x)}{v(x)}\right)'=\dfrac{u'(x)\cdot v(x)-u(x)\cdot v'(x)}{(v(x))^2}$

## ⟦Integrallarga doir formulalar||Таблица интегралов⟧
- $\displaystyle\int x^n dx=\dfrac{x^{n+1}}{n+1}+C$; $\; \displaystyle\int\dfrac{dx}{x}=\ln\lvert x\rvert+C$; $\; \displaystyle\int e^x dx=e^x+C$
- $\displaystyle\int a^x dx=\dfrac{a^x}{\ln a}+C$; $\; \displaystyle\int\sin x\,dx=-\cos x+C$; $\; \displaystyle\int\cos x\,dx=\sin x+C$

## ⟦Integrallarning xossalari||Свойства интегралов⟧
- $\displaystyle\int k\cdot f(x)dx=k\cdot\int f(x)dx$; $\; \displaystyle\int(f(x)+g(x))dx=\int f(x)dx+\int g(x)dx$
- $\displaystyle\int_a^a f(x)dx=0$; $\; \displaystyle\int_a^b f(x)dx=F(x)\Big|_a^b=F(b)-F(a)$
- $\displaystyle\int_a^b f(x)dx=-\int_b^a f(x)dx$; $\; \displaystyle\int_a^b f(x)dx=\int_a^c f(x)dx+\int_c^b f(x)dx$, $a\le c\le b$

## ⟦O‘rta arifmetik va o‘rta geometrik||Среднее арифметическое и среднее геометрическое⟧
- $A=\dfrac{a_1+a_2+a_3+\ldots+a_n}{n}$; $\quad G=\sqrt[n]{a_1\cdot a_2\cdot a_3\cdots a_n}$

## ⟦Ba’zi trigonometrik formulalar||Основные формулы тригонометрии⟧
- $\cos(\alpha\pm\beta)=\cos\alpha\cos\beta\mp\sin\alpha\sin\beta$
- $\sin(\alpha\pm\beta)=\sin\alpha\cos\beta\pm\cos\alpha\sin\beta$
- $\operatorname{tg}(\alpha\pm\beta)=\dfrac{\operatorname{tg}\alpha\pm\operatorname{tg}\beta}{1\mp\operatorname{tg}\alpha\operatorname{tg}\beta}$; $\; \operatorname{ctg}(\alpha\pm\beta)=\dfrac{\operatorname{ctg}\alpha\operatorname{ctg}\beta\mp1}{\operatorname{ctg}\alpha\pm\operatorname{ctg}\beta}$
- $\sin\alpha+\sin\beta=2\sin\dfrac{\alpha+\beta}{2}\cos\dfrac{\alpha-\beta}{2}$; $\; \sin\alpha-\sin\beta=2\sin\dfrac{\alpha-\beta}{2}\cos\dfrac{\alpha+\beta}{2}$
- $\cos\alpha+\cos\beta=2\cos\dfrac{\alpha+\beta}{2}\cos\dfrac{\alpha-\beta}{2}$; $\; \cos\alpha-\cos\beta=-2\sin\dfrac{\alpha-\beta}{2}\sin\dfrac{\alpha+\beta}{2}$

## ⟦Asosiy trigonometrik ayniyatlar||Основные тригонометрические тождества⟧
- $\sin^2\alpha+\cos^2\alpha=1$; $\; \operatorname{tg}\alpha=\dfrac{\sin\alpha}{\cos\alpha}$; $\; \operatorname{ctg}\alpha=\dfrac{\cos\alpha}{\sin\alpha}$
- $\operatorname{tg}^2\alpha+1=\dfrac{1}{\cos^2\alpha}$; $\; \operatorname{ctg}^2\alpha+1=\dfrac{1}{\sin^2\alpha}$

## ⟦Trigonometrik funksiyaning ba’zi burchaklardagi qiymatlari||Значения тригонометрических функций некоторых углов⟧

| $\alpha$ | $0$ | $\frac{\pi}{6}$ | $\frac{\pi}{4}$ | $\frac{\pi}{3}$ | $\frac{\pi}{2}$ |
|---|---|---|---|---|---|
| $\sin\alpha$ | $0$ | $\frac{1}{2}$ | $\frac{\sqrt2}{2}$ | $\frac{\sqrt3}{2}$ | $1$ |
| $\cos\alpha$ | $1$ | $\frac{\sqrt3}{2}$ | $\frac{\sqrt2}{2}$ | $\frac{1}{2}$ | $0$ |

## ⟦Ixtiyoriy uchburchak uchun formulalar||Формулы для произвольного треугольника⟧
- $S=\dfrac12 ab\sin\gamma$; $\; S=\sqrt{p(p-a)(p-b)(p-c)}$; $\; p=\dfrac12(a+b+c)$; $\; S=\dfrac12 h_c c$
- $\dfrac{a}{\sin\alpha}=\dfrac{b}{\sin\beta}=\dfrac{c}{\sin\gamma}$; $\; a^2=b^2+c^2-2bc\cos\alpha$

## ⟦To‘g‘ri burchakli uchburchak uchun formulalar||Формулы для прямоугольного треугольника⟧
- $a^2+b^2=c^2$; $\; a=c\cdot\sin\alpha$; $\; b=c\cdot\cos\alpha$; $\; a=b\cdot\operatorname{tg}\alpha$

## ⟦Uchburchakka ichki va tashqi chizilgan aylana radiuslari||Радиусы вписанной и описанной окружностей треугольника⟧
- $r=\dfrac{2S}{a+b+c}$; $\; R=\dfrac{abc}{4S}$; $\; R=\dfrac{a}{2\sin\alpha}=\dfrac{b}{2\sin\beta}=\dfrac{c}{2\sin\gamma}$

## ⟦To‘rtburchaklarning yuzalari||Площади четырёхугольников⟧
- ⟦Parallelogramm||Параллелограмм⟧: $S=a\cdot h_a$; $\; S=a\cdot b\cdot\sin\alpha$
- ⟦Romb||Ромб⟧: $S=\dfrac12 d_1\cdot d_2$; $\; S=a^2\cdot\sin\alpha$
- ⟦Trapetsiya||Трапеция⟧: $S=\dfrac{a+b}{2}\cdot h$

## ⟦Vektorlar||Векторы⟧
- $\lvert\vec a\rvert=\sqrt{x^2+y^2+z^2}$ — ⟦$\vec a(x,y,z)$ vektorning uzunligi||длина вектора $\vec a(x,y,z)$⟧
- $\vec a\cdot\vec b=\lvert\vec a\rvert\cdot\lvert\vec b\rvert\cdot\cos\varphi$ — ⟦skalyar ko‘paytma||скалярное произведение⟧
- $\vec a(x_1;y_1)$, $\vec b(x_2;y_2)$: $\; \vec a\cdot\vec b=x_1\cdot x_2+y_1\cdot y_2$; $\; \vec a\cdot\lambda=\vec c(x\cdot\lambda;\ y\cdot\lambda;\ z\cdot\lambda)$

## ⟦Aylana va doira||Окружность и круг⟧
- $l=2\pi R$; $\; S=\pi R^2$

## ⟦Doiraviy sektor va segment yuzi||Площадь кругового сектора и сегмента⟧
- $S_{sek.}=\dfrac{\pi R^2}{360}\cdot\alpha$; $\; S_{segm.}=\dfrac{R^2}{2}(\alpha-\sin\alpha)$

## ⟦Stereometriya formulalari||Формулы стереометрии⟧
- ⟦Prizma||Призма⟧: $V=SH$
- ⟦Piramida||Пирамида⟧: $V=\dfrac13 SH$
- ⟦Kesik piramida||Усечённая пирамида⟧: $V=\dfrac13 h\left(S_1+\sqrt{S_1\cdot S_2}+S_2\right)$
- ⟦Silindr||Цилиндр⟧: $S_{yon}=2\pi RH$; $\; V=\pi R^2H$
- ⟦Konus||Конус⟧: $S_{yon}=\pi Rl$; $\; V=\dfrac13\pi R^2H$
- ⟦Kesik konus||Усечённый конус⟧: $V=\dfrac13\pi h\left(R_1^2+R_1\cdot R_2+R_2^2\right)$
- ⟦Shar||Шар⟧: $S=4\pi R^2$; $\; V=\dfrac43\pi R^3$
- ⟦Shar segmentining hajmi||Объём шарового сегмента⟧: $V=\pi H^2\left(R-\dfrac{H}{3}\right)$
- ⟦Shar segmentining sirtining yuzi||Площадь поверхности сегмента шара⟧: $S=2\pi RH$

*⟦Eslatma: bu formulalar yordam sifatida tavsiya qilinadi.||Памятка: данные формулы предоставляются в качестве вспомогательного материала.⟧*
"""

PHYS = r"""
## ⟦Mexanika||Механика⟧
- $v=\dfrac{\Delta s}{\Delta t}$; $\; a=\dfrac{\Delta v}{\Delta t}$; $\; s=v_0t+\dfrac{at^2}{2}$; $\; \omega=\dfrac{\Delta\varphi}{\Delta t}$; $\; \varepsilon=\dfrac{\Delta\omega}{\Delta t}$; $\; \varphi=\omega_0t+\dfrac{\varepsilon t^2}{2}$
- $\omega=2\pi\nu$; $\; v=\omega r$; $\; \nu\cdot T=1$; $\; v=v_0\pm gt$; $\; h=v_0t\pm\dfrac{gt^2}{2}$
- $v_{0x}=v_0\cdot\cos\alpha$; $\; v_{0y}=v_0\cdot\sin\alpha$; $\; t_u=\dfrac{2v_{0y}}{g}$; $\; h_{max}=\dfrac{v_{0y}^2}{2g}$; $\; s=v_{0x}\cdot t_u$
- $\vec a=\vec a_\tau+\vec a_n$; $\; a_n=\dfrac{v^2}{r}$; $\; m=\rho V$; $\; \vec a=\dfrac{\vec F}{m}$; $\; \vec F_1=-\vec F_2$; $\; F_{el}=-k\Delta l$
- $a=g(\sin\alpha\pm\mu\cos\alpha)$; $\; \vec p=m\vec v$; $\; \vec F\Delta t=\Delta\vec p$; $\; E_k=\dfrac{mv^2}{2}$
- $M=Fl$; $\; F_1l_1=F_2l_2$; $\; F_{ish}=\mu N$; $\; N=\vec F\cdot\vec v$
- $A=F\cdot S\cdot\cos\alpha$; $\; E_p=mgh$; $\; E_k+E_p=const$; $\; P=m(\vec g-\vec a)$
- $g=\dfrac{GM}{R^2}$; $\; v_I=\sqrt{gR}$; $\; v_{II}=\sqrt{2gR}$; $\; x=A\cdot\sin(\omega t+\varphi_0)$; $\; v=x'$
- $a=v'$; $\; v=A\omega\cos(\omega t+\varphi_0)$; $\; a=-x\cdot\omega^2$; $\; v=\lambda\nu$; $\; v=\sqrt{\dfrac{T}{\rho_{ch}}}$
- $v=\sqrt{\dfrac{E}{\rho}}$; $\; \omega=\sqrt{\dfrac{k}{m}}$; $\; T=2\pi\sqrt{\dfrac{m}{k}}$; $\; \omega=\sqrt{\dfrac{g}{l}}$; $\; T=2\pi\sqrt{\dfrac{l}{g}}$; $\; \Delta l=l-l_0$
- $\varepsilon=\dfrac{\Delta l}{l_0}$; $\; k=\dfrac{ES}{l_0}$; $\; F_A=\rho_s V_b g$; $\; p=\rho gh$; $\; S_1v_1=S_2v_2$
- $V_b=\dfrac{\rho_1V_1}{\rho_s}$; $\; p+\dfrac{\rho v^2}{2}+\rho gh=const$

## ⟦Molekulyar fizika||Молекулярная физика⟧
- $\nu=\dfrac{N}{N_A}=\dfrac{m}{M}$; $\; n=\dfrac{N}{V}$; $\; d=\sqrt[3]{\dfrac{VM}{mN_A}}$; $\; \rho=nm_0$
- $p=\dfrac23n\bar E_k=\dfrac{\rho\bar v^2}{3}=nkT$; $\; \bar E_k=\dfrac{m_0\bar v^2}{2}=\dfrac32kT$
- $\bar v=\sqrt{\dfrac{3RT}{\mu}}=\sqrt{\dfrac{3kT}{m_0}}$; $\; T=t+273$
- $pV=\nu RT$; $\; p=\dfrac{\rho}{M}RT$; $\; \dfrac{pV}{T}=const$; $\; Q=A+\Delta U$
- $A=p\Delta V$; $\; \Delta U=\dfrac32(p_2V_2-p_1V_1)=\dfrac32\nu R\Delta T$; $\; C=\dfrac{Q}{T_2-T_1}$
- $c=\dfrac{Q}{m(T_2-T_1)}$; $\; \lambda=\dfrac{Q}{m}$; $\; r=\dfrac{Q}{m}$; $\; q=\dfrac{Q}{m}$
- $\eta=\dfrac{Q_1-Q_2}{Q_1}\cdot100\%=\dfrac{T_1-T_2}{T_1}\cdot100\%$; $\; F=\sigma l$
- $\sigma=\dfrac{F}{S}$; $\; \sigma=E\cdot\lvert\varepsilon\rvert$; $\; W=\sigma S$; $\; h=\dfrac{2\sigma}{\rho gr}$; $\; \Delta p=\dfrac{2\sigma}{R}$
- $\rho=\dfrac{m}{V}$; $\; \varphi=\dfrac{\rho}{\rho_0}\cdot100\%=\dfrac{p}{p_0}\cdot100\%$

## ⟦Elektr va magnetizm||Электричество и магнетизм⟧
- $F=\dfrac{k\lvert qQ\rvert}{\varepsilon r^2}$; $\; E=\dfrac{k\lvert Q\rvert}{\varepsilon r^2}$; $\; F=qE$; $\; \varphi=\dfrac{kQ}{\varepsilon r}$; $\; W_p=q\varphi$
- $E=\dfrac{\varphi_1-\varphi_2}{d}$; $\; A=q(\varphi_1-\varphi_2)$; $\; W_{el}=\dfrac{qU}{2}$; $\; C=\dfrac{\varepsilon\varepsilon_0S}{d}$; $\; q=CU$
- $w=\dfrac{\varepsilon\varepsilon_0E^2}{2}$; $\; C_p=C_1+C_2+\ldots+C_N$; $\; \dfrac{1}{C_{ket}}=\dfrac{1}{C_1}+\dfrac{1}{C_2}+\ldots+\dfrac{1}{C_n}$
- $E=\dfrac{U}{d}=\dfrac{\sigma}{\varepsilon\varepsilon_0}$; $\; I=\dfrac{U}{R}$; $\; Q=I^2Rt$; $\; P=IU$; $\; I=ne\bar vS$; $\; j=\dfrac{I}{S}$
- $q=It$; $\; E=\rho j$; $\; R=\dfrac{\rho l}{S}$; $\; R=R_0(1+\alpha\Delta t)$; $\; R_{ket}=R_1+R_2+\ldots+R_N$
- $\dfrac{1}{R_p}=\dfrac{1}{R_1}+\dfrac{1}{R_2}+\ldots+\dfrac{1}{R_N}$; $\; \varepsilon=\dfrac{A_{chet}}{q}$; $\; I=\dfrac{\varepsilon}{R+r}$; $\; \eta=\dfrac{R}{R+r}=\dfrac{U}{\varepsilon}$
- $I_a=kU^{3/2}$; $\; T=2\pi\sqrt{LC}$; $\; \omega=\dfrac{1}{\sqrt{LC}}$; $\; W=\dfrac{q^2}{2C}+\dfrac{L\cdot I^2}{2}$
- $Z=\sqrt{R^2+\left(\omega L-\dfrac{1}{\omega C}\right)^2}$; $\; I=\dfrac UZ$; $\; \cos\varphi=\dfrac RZ$; $\; P=I^2R=IU\cos\varphi$
- $I=\dfrac{I_0}{\sqrt2}$; $\; U=\dfrac{U_0}{\sqrt2}$; $\; B=\dfrac{\mu_0I}{2\pi R}$; $\; B=\dfrac{\mu_0I}{2R}$; $\; F=\dfrac{\mu_0I_1I_2}{2\pi d}l$
- $F_A=IBl\sin\alpha$; $\; F_L=q\upsilon B\sin\alpha$; $\; R=\dfrac{m\upsilon}{qB}$; $\; T=\dfrac{2\pi m}{qB}$; $\; \omega=\dfrac{qB}{m}$
- $\Phi=NBS\cos\alpha$; $\; \Phi=IL$; $\; W=\dfrac{I\Phi}{2}=\dfrac{LI^2}{2}$; $\; \varepsilon=-\dfrac{\Delta\Phi}{\Delta t}=-L\dfrac{\Delta I}{\Delta t}$

## ⟦Optika va kvant fizikasi. Atom va yadro fizikasi. Nisbiylik nazariyasi||Оптика и квантовая физика. Атомная и ядерная физика. Теория относительности⟧
- $n=\dfrac cv=\sqrt{\varepsilon\mu}$; $\; \dfrac{\sin\alpha}{\sin\beta}=\dfrac{n_2}{n_1}$; $\; \pm\dfrac1F=\dfrac1d\pm\dfrac1f$; $\; D=\pm\dfrac1F$
- $k=\dfrac fd$; $\; \dfrac1F=\left(\dfrac{n_l}{n_m}-1\right)\left(\dfrac1{R_1}+\dfrac1{R_2}\right)$; $\; I=\dfrac{P}{S}=wv$; $\; I\sim\omega^4$
- $d\cdot\sin\alpha=n\lambda$; $\; \lambda_m=\dfrac bT$; $\; I=\dfrac{I_0}{2}$; $\; I=I_0\cos^2\alpha$; $\; I=\dfrac\Phi\Omega$
- $E=\dfrac\Phi S=\dfrac{I}{R^2}\cos\varphi$; $\; E=h\nu$; $\; p=\dfrac{h\nu}{c}=\dfrac h\lambda$; $\; I=\dfrac{N}{S\cdot t}h\nu$
- $h\nu=A+E_{k\,max}$; $\; E_{k\,max}=eU_{yop}$; $\; h\nu_{min}=\dfrac{hc}{\lambda_{max}}=A$
- $E_n=\dfrac{E_1}{n^2}$; $\; E_1=-13{,}6\ \text{eV}$; $\; h\nu=E_n-E_m$; $\; m_ev_nr_n=n\hbar$
- $r_n=n^2r_B$; $\; E_{bog'}=\Delta mc^2$; $\; E_{sol}=\dfrac{E_{bog'}}{A}$; $\; A=-\dfrac{dN}{dt}$
- $N=N_0e^{-\lambda t}=N_02^{-t/T}$; $\; \lambda T=\ln2\approx0{,}7$
- $\tau=\dfrac{\tau_0}{\sqrt{1-\upsilon^2/c^2}}$; $\; l=l_0\sqrt{1-\upsilon^2/c^2}$; $\; \upsilon_2=\dfrac{\upsilon_1\pm\upsilon}{1\pm\upsilon_1\upsilon/c^2}$
- $m=\dfrac{m_0}{\sqrt{1-\upsilon^2/c^2}}$; $\; E_0=m_0c^2$; $\; E=mc^2$; $\; \vec p=m\vec\upsilon$
- $E_k=(m-m_0)c^2$; $\; E^2-c^2p^2=m_0^2c^4$

*⟦Eslatma: bu formulalar yordam sifatida tavsiya qilinadi.||Памятка: данные формулы предоставляются в качестве вспомогательного материала.⟧*

## ⟦Fizik doimiylar va shartli belgilar||Физические постоянные и условные обозначения⟧

### ⟦O‘nli old qo‘shimchalar||Десятичные приставки⟧

| ⟦Belgilanishi||Обозн.⟧ | ⟦Old qo‘shimcha||Приставка⟧ | ⟦Ko‘paytuvchi||Множитель⟧ |
|---|---|---|
| T | tera / тера | $10^{12}$ |
| G | giga / гига | $10^{9}$ |
| M | mega / мега | $10^{6}$ |
| k | kilo / кило | $10^{3}$ |
| d | detsi / деци | $10^{-1}$ |
| c | santi / санти | $10^{-2}$ |
| m | milli / милли | $10^{-3}$ |
| $\mu$ | mikro / микро | $10^{-6}$ |
| n | nano / нано | $10^{-9}$ |
| p | piko / пико | $10^{-12}$ |

### ⟦Doimiy fizik kattaliklar||Физические постоянные⟧

| ⟦Kattalik||Величина⟧ | ⟦Qiymati||Значение⟧ |
|---|---|
| ⟦Yer sirti yaqinida erkin tushish tezlanishi||Ускорение свободного падения вблизи Земли⟧ | $g\approx10\ \text{m/s}^2$ |
| ⟦Gravitatsion doimiy||Гравитационная постоянная⟧ | $G=\frac{20}{3}\cdot10^{-11}\ \text{N}\cdot\text{m}^2/\text{kg}^2$ |
| ⟦Universal gaz doimiysi||Универсальная газовая постоянная⟧ | $R=8{,}31\ \text{J}/(\text{mol}\cdot\text{K})$ |
| ⟦Bolsman doimiysi||Постоянная Больцмана⟧ | $k=1{,}38\cdot10^{-23}\ \text{J/K}$ |
| ⟦Avogadro soni||Число Авогадро⟧ | $N_A=6\cdot10^{23}\ \text{mol}^{-1}$ |
| ⟦Elementar zaryad||Элементарный заряд⟧ | $e=1{,}6\cdot10^{-19}\ \text{C}$ |
| ⟦Kulon qonuni uchun proporsionallik koeffitsiyenti||Коэффициент пропорциональности закона Кулона⟧ | $k=9\cdot10^{9}\ \text{N}\cdot\text{m}^2/\text{C}^2$ |
| ⟦Elektr doimiysi||Электрическая постоянная⟧ | $\varepsilon_0=8{,}85\cdot10^{-12}\ \text{F/m}$ |
| ⟦Magnit doimiysi||Магнитная постоянная⟧ | $\mu_0=4\pi\cdot10^{-7}\ \text{N/A}^2$ |
| ⟦Yorug‘likning vakuumdagi tezligi||Скорость света в вакууме⟧ | $c=3\cdot10^{8}\ \text{m/s}$ |
| ⟦Plank doimiysi||Постоянная Планка⟧ | $h=4{,}125\cdot10^{-15}\ \text{eV}\cdot\text{s}=6{,}6\cdot10^{-34}\ \text{J}\cdot\text{s}$ |

### ⟦Shartli belgilar||Условные обозначения⟧
- $\times\ \times$ — ⟦magnit induksiya chiziqlari qog‘oz tekisligiga tik yo‘nalgan (kuzatuvchidan qog‘oz tekisligiga)||линии магнитной индукции направлены от наблюдателя перпендикулярно к плоскости рисунка⟧
- $\bullet\ \bullet$ — ⟦magnit induksiya chiziqlari qog‘oz tekisligiga tik ravishda kuzatuvchiga yo‘nalgan||линии магнитной индукции направлены перпендикулярно плоскости рисунка к наблюдателю⟧
- $\oplus$ — ⟦o‘tkazgichdagi tok qog‘oz tekisligiga tik, kuzatuvchidan uzoqqa yo‘nalgan||ток в проводнике направлен от наблюдателя перпендикулярно к плоскости рисунка⟧
- $\odot$ — ⟦o‘tkazgichdagi tok qog‘oz tekisligiga tik, kuzatuvchiga yo‘nalgan||ток в проводнике направлен перпендикулярно плоскости рисунка к наблюдателю⟧

## ⟦Moddalar va ularning xossalari||Вещества и их свойства⟧

### ⟦Zichlik||Плотность⟧, $\text{kg/m}^3$

| ⟦Modda||Вещество⟧ | $\rho$ | ⟦Modda||Вещество⟧ | $\rho$ |
|---|---|---|---|
| ⟦benzin||бензин⟧ | 700 | ⟦alyuminiy||алюминий⟧ | 2700 |
| ⟦kerosin||керосин⟧ | 800 | ⟦muz||лёд⟧ | 900 |
| ⟦suv (4 °C)||вода (4 °C)⟧ | 1000 | ⟦mis||медь⟧ | 8900 |
| ⟦spirt||спирт⟧ | 800 | ⟦po‘lat||сталь⟧ | 7800 |
| ⟦simob||ртуть⟧ | 13600 | ⟦temir||железо⟧ | 7800 |

### ⟦Molyar massa||Молярная масса⟧, $\text{g/mol}$

| ⟦Modda||Вещество⟧ | | $M$ | ⟦Modda||Вещество⟧ | | $M$ |
|---|---|---|---|---|---|
| ⟦argon||аргон⟧ | Ar | 40 | ⟦karbonat angidrid||двуокись углерода⟧ | $\text{CO}_2$ | 44 |
| ⟦azot||азот⟧ | $\text{N}_2$ | 28 | ⟦mis||медь⟧ | Cu | 64 |
| ⟦geliy||гелий⟧ | He | 4 | ⟦alyuminiy||алюминий⟧ | Al | 27 |
| ⟦neon||неон⟧ | Ne | 20 | ⟦kislorod||кислород⟧ | $\text{O}_2$ | 32 |
| ⟦havo||воздух⟧ | | 29 | ⟦vodorod||водород⟧ | $\text{H}_2$ | 2 |
| ⟦suv||вода⟧ | $\text{H}_2\text{O}$ | 18 | | | |

### ⟦Solishtirma issiqlik sig‘imi||Удельная теплоёмкость⟧, $\text{J/(kg}\cdot\text{K)}$

| ⟦Modda||Вещество⟧ | $c$ | ⟦Modda||Вещество⟧ | $c$ |
|---|---|---|---|
| ⟦alyuminiy||алюминий⟧ | 900 | ⟦sink||цинк⟧ | 400 |
| ⟦mis||медь⟧ | 380 | ⟦suv||вода⟧ | 4200 |
| ⟦muz||лёд⟧ | 2100 | ⟦temir||железо⟧ | 450 |
| ⟦oltin||золото⟧ | 120 | ⟦cho‘yan||чугун⟧ | 500 |

### ⟦Solishtirma erish issiqligi||Удельная теплота плавления⟧, $10^5\ \text{J/kg}$
- ⟦muz (0 °C)||лёд (0 °C)⟧: $330$

### ⟦Solishtirma bug‘lanish issiqligi||Удельная теплота испарения⟧, $10^6\ \text{J/kg}$
- ⟦suv (100 °C)||вода (100 °C)⟧: $2{,}3$

### ⟦Yoqilg‘ining solishtirma yonish issiqligi||Удельная теплотворность горючего⟧, $10^6\ \text{J/kg}$

| ⟦Yoqilg‘i||Топливо⟧ | $q$ | ⟦Yoqilg‘i||Топливо⟧ | $q$ |
|---|---|---|---|
| ⟦benzin||бензин⟧ | 46 | ⟦tabiiy gaz||природный газ⟧ | 44 |
| ⟦neft||нефть⟧ | 44 | ⟦toshko‘mir||каменный уголь⟧ | 29 |
| ⟦spirt||спирт⟧ | 29 | ⟦yog‘och||дерево⟧ | 10 |

### ⟦Sirt taranglik koeffitsiyenti (20 °C)||Коэффициент поверхностного натяжения (20 °C)⟧, $10^{-3}\ \text{N/m}$

| ⟦Modda||Вещество⟧ | $\sigma$ | ⟦Modda||Вещество⟧ | $\sigma$ |
|---|---|---|---|
| ⟦benzin||бензин⟧ | 21 | ⟦spirt||спирт⟧ | 22 |
| ⟦kerosin||керосин⟧ | 24 | ⟦sovun eritmasi||мыльный раствор⟧ | 40 |
| ⟦suv||вода⟧ | 73 | ⟦simob||ртуть⟧ | 510 |

### ⟦O‘tkazgichlarning solishtirma qarshiligi (20 °C)||Удельное сопротивление проводников (20 °C)⟧, $10^{-8}\ \Omega\cdot\text{m}$

| ⟦Modda||Вещество⟧ | $\rho$ | ⟦Modda||Вещество⟧ | $\rho$ |
|---|---|---|---|
| ⟦mis||медь⟧ | 1,7 | ⟦temir||железо⟧ | 9,8 |
| ⟦alyuminiy||алюминий⟧ | 2,8 | ⟦nikelin||никелин⟧ | 40 |
| ⟦volfram||вольфрам⟧ | 5,5 | ⟦nixrom||нихром⟧ | 110 |

### ⟦Nur sindirish ko‘rsatkichi||Показатель преломления некоторых веществ⟧

| ⟦Modda||Вещество⟧ | $n$ | ⟦Modda||Вещество⟧ | $n$ |
|---|---|---|---|
| ⟦suv||вода⟧ | $4/3$ | ⟦yoqut||рубин⟧ | 1,76 |
| ⟦shisha||стекло⟧ | 1,5 | ⟦olmos||алмаз⟧ | 2,42 |

### ⟦Ayrim birliklar o‘rtasidagi munosabat||Соотношения между некоторыми единицами⟧
- $0\,°\text{C}=273\ \text{K}$; $\; 1\ \text{u}=1{,}66\cdot10^{-27}\ \text{kg}$
- $1\ \text{eV}=1{,}6\cdot10^{-19}\ \text{J}$; $\; 1\ \text{mm Hg}=133{,}3\ \text{Pa}$

### ⟦Normal sharoit||Нормальные условия⟧
- ⟦bosim||давление⟧: $10^5\ \text{Pa}$; ⟦temperatura||температура⟧: $0\,°\text{C}$
"""

CHEM = r"""
## ⟦Kimyoviy formulalar||Химические формулы⟧

### ⟦Organik moddalar — umumiy formulasi||Органические вещества — общая формула⟧

| ⟦Organik moddalar||Органические вещества⟧ | ⟦Umumiy formulasi||Общая формула⟧ |
|---|---|
| ⟦Alkanlar||Алканы⟧ | $C_nH_{2n+2}$ |
| ⟦Sikloalkanlar, alkenlar||Циклоалканы, алкены⟧ | $C_nH_{2n}$ |
| ⟦Alkadiyenlar, alkinlar||Алкадиены, алкины⟧ | $C_nH_{2n-2}$ |
| ⟦Arenlar||Арены⟧ | $C_nH_{2n-6}$ |
| ⟦To‘yingan bir atomli spirtlar, to‘yingan oddiy efirlar||Насыщенные одноатомные спирты, насыщенные простые эфиры⟧ | $C_nH_{2n+2}O$ |
| ⟦Aldegidlar, ketonlar||Альдегиды, кетоны⟧ | $C_nH_{2n}O$ |
| ⟦To‘yingan monokarbon kislotalar, to‘yingan murakkab efirlar||Насыщенные монокарбоновые кислоты, насыщенные сложные эфиры⟧ | $C_nH_{2n}O_2$ |

### ⟦Modda miqdori||Количество вещества⟧
- $n=\dfrac mM$; $\; \rho=\dfrac mV$; $\; \rho_{(gaz)}=\dfrac{M}{V_m}$
- $V=V_m\cdot n$; $\; N=N_A\cdot n$; $\; D_{H_2}=\dfrac{M}{M(H_2)}$
- $PVM=mRT$

### ⟦Kimyoviy kinetika||Химическая кинетика⟧
- $aA+bB\rightleftharpoons cC+dD$; $\; K_M=\dfrac{k_2}{k_1}=\dfrac{[C]^c\cdot[D]^d}{[A]^a\cdot[B]^b}$
- $v=\dfrac{C}{t}$; $\; v_2=v_1\cdot\gamma^{\frac{T_2-T_1}{10}}$
- $aA+bB\to cC$; $\; v=k\cdot[A]^{(a)}\cdot[B]^{(b)}$

### ⟦Eritmalar va ulardagi jarayonlar||Растворы и процессы, происходящие в растворах⟧
- $AB\rightleftharpoons A^++B^-$; $\; K_{dis}=\dfrac{[A^+]\cdot[B^-]}{[AB]}$; $\; m=\dfrac{E\cdot I\cdot t_{(s)}}{96500}$
- $C_\%=\dfrac{m_1}{m_2}\cdot100\%$; $\; C_M=\dfrac{n}{V_{(litr)}}$; $\; C_N=\dfrac{n_{ekv}}{V_{(litr)}}$
- $C_M=\dfrac{C_\%\cdot10\cdot\rho}{M}$; $\; C_N=\dfrac{C_\%\cdot10\cdot\rho}{E}$
- $C_N=C_M\cdot Val\cdot n(kat)$

### ⟦Ekvivalent||Эквивалент⟧
- $E=\dfrac{A_r}{V(\text{valentlik})}$; $\; \dfrac{m_1}{m_2}=\dfrac{E_1}{E_2}$
- $E_{oksid}=\dfrac{M}{V\cdot n}$; $\; E_{tuz}=\dfrac{M}{V\cdot n}$
- $E_{kislota}=\dfrac{M}{n(H)}$; $\; E_{asos}=\dfrac{M}{n(OH)}$

### ⟦Nisbiy atom massa||Относительная атомная масса⟧
- $A_r=N+Z$

*⟦Eslatma: bu formulalar yordam sifatida tavsiya qilinadi.||Памятка: данные формулы предоставляются в качестве вспомогательного материала.⟧*

## ⟦Moddalarning suvda eruvchanlik jadvali||Таблица растворимости веществ в воде⟧

⟦**E** — eriydi; **O** — oz eriydi; **Q** — qiyin eriydi; **•** — erimaydi (cho‘kma); **—** bunday birikma mavjud emas yoki suvda parchalanadi.||**E** — растворимое; **O** — малорастворимое; **Q** — труднорастворимое; **•** — нерастворимое (осадок); **—** такое соединение не существует или разлагается водой.⟧

| ⟦Anion \ Kation||Анион \ Катион⟧ | $H^+$ | $NH_4^+$ | $Na^+,K^+$ | $Mg^{2+}$ | $Ca^{2+}$ | $Ba^{2+}$ | $Sr^{2+}$ | $Li^+$ | $Zn^{2+}$ | $Hg^{2+}$ | $Mn^{2+}$ | $Co^{2+},Ni^{2+}$ | $Cd^{2+}$ | $Fe^{2+}$ | $Cu^{2+}$ | $Ag^+$ | $Sn^{2+}$ | $Pb^{2+}$ | $Bi^{3+}$ | $Al^{3+}$ | $Fe^{3+}$ | $Cr^{3+}$ |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| $OH^-$ | | E | E | O | O | E | E | E | Q | — | Q | Q | Q | Q | Q | — | Q | Q | • | Q | Q | Q |
| $F^-$ | E | E | E | Q | Q | O | O | O | E | — | O | E | Q | E | Q | E | O | Q | — | O | Q | Q |
| $Cl^-$ | E | E | E | E | E | E | E | E | E | E | E | E | E | E | E | Q | E | O | E | E | E | E |
| $Br^-$ | E | E | E | E | E | E | E | E | E | O | E | E | E | E | E | Q | E | O | E | E | E | E |
| $I^-$ | E | E | E | E | E | E | E | E | E | Q | E | E | E | E | — | Q | E | Q | Q | E | — | E |
| $S^{2-}$ | E | — | E | O | O | E | O | E | • | • | • | • | • | • | • | • | • | • | • | — | — | — |
| $SO_3^{2-}$ | E | E | E | • | • | • | • | E | • | • | • | • | • | • | • | • | — | • | • | — | — | — |
| $SO_4^{2-}$ | E | E | E | E | O | • | • | E | E | E | E | E | E | E | E | O | E | • | E | E | E | E |
| $NO_3^-$ | E | E | E | E | E | E | E | E | E | E | E | E | E | E | E | E | E | E | E | E | E | E |
| $PO_4^{3-}$ | E | E | E | • | • | • | • | Q | • | • | • | • | • | • | • | • | • | • | • | • | • | • |
| $CO_3^{2-}$ | E | E | E | • | • | • | • | Q | • | • | • | • | • | • | — | Q | — | • | • | — | — | — |
| $SiO_3^{2-}$ | • | — | E | • | • | • | • | Q | • | — | • | • | • | • | — | Q | — | • | • | — | — | — |
| $CrO_4^{2-}$ | E | E | E | E | E | Q | Q | E | Q | Q | — | • | • | — | • | • | — | • | • | — | — | — |
| $CH_3COO^-$ | E | E | E | E | E | E | E | E | E | E | E | E | E | E | E | O | E | E | — | E | — | E |

*⟦Jadvalning ba’zi katakchalari skanerlangan asl nusxada aniq o‘qilmaydi; to‘liq jadval imtihon varaqasida beriladi.||Некоторые ячейки таблицы плохо читаются в скане оригинала; полная таблица выдаётся на экзамене.⟧*

## ⟦Metallarning elektrokimyoviy kuchlanish qatori||Электрохимический ряд напряжений металлов⟧
$\text{Li, Rb, K, Ba, Sr, Ca, Na, Mg, Al, Be, Mn, Zn, Cr, Ga, Fe, Cd, Tl, Co, Ni, Sn, Pb, H, Cu, Hg, Ag, Pt, Au}$

## ⟦Kimyoviy elementlarning davriy sistemasi||Периодическая система химических элементов⟧
⟦Davriy sistema imtihon varaqasida rangli jadval ko‘rinishida beriladi (davrlar I–VII, guruhlar I–VIII, lantanoidlar va aktinoidlar).||Периодическая система выдаётся на экзамене в виде цветной таблицы (периоды I–VII, группы I–VIII, лантаноиды и актиноиды).⟧
"""

SHEETS = {"math": MATH, "physics": PHYS, "chemistry": CHEM}


async def main() -> None:
    async with httpx.AsyncClient(base_url=API, timeout=30) as http:
        r = await http.post("/v1/identity/login", json={"email": EMAIL, "password": PASSWORD})
        r.raise_for_status()
        http.headers["Authorization"] = f"Bearer {r.json()['access_token']}"
        subjects = {
            s["code"]: s["id"] for s in (await http.get("/v1/admin/catalog/subjects")).json()
        }
        for code, src in SHEETS.items():
            sid = subjects.get(code)
            if sid is None:
                print(f"skip {code}: subject not found")
                continue
            contents = {loc: render(src, loc) for loc in ("uz-Latn", "ru")}
            put = await http.put(
                f"/v1/admin/catalog/subjects/{sid}/reference",
                json={"contents": contents, "source": SOURCE["uz-Latn"], "active": True},
            )
            put.raise_for_status()
            print(f"{code}: {sorted(put.json()['contents'])} ok")


if __name__ == "__main__":
    asyncio.run(main())
