from .cleaning import coerce_str
COLOR_BUCKETS = {"ağ":"Ağ","ag":"Ağ","white":"Ağ","qara":"Qara","black":"Qara","boz":"Boz","gray":"Boz","grey":"Boz",
"gümüş":"Gümüş","gumus":"Gümüş","silver":"Gümüş","göy":"Göy","mavi":"Göy","blue":"Göy","qırmızı":"Qırmızı","red":"Qırmızı",
"yaşıl":"Yaşıl","yasil":"Yaşıl","green":"Yaşıl","sarı":"Sarı","sari":"Sarı","yellow":"Sarı","bej":"Bej","beige":"Bej",
"qəhvəyi":"Qəhvəyi","qehveyi":"Qəhvəyi","brown":"Qəhvəyi","bənövşəyi":"Bənövşəyi","benevseyi":"Bənövşəyi","purple":"Bənövşəyi",
"narıncı":"Narıncı","narinci":"Narıncı","orange":"Narıncı","qızılı":"Qızılı","gold":"Qızılı"}
def normalize_color(c):
    c0 = (coerce_str(c) or "").lower()
    c0 = c0.replace("metallik","").replace("metallic","").strip()
    for k,v in COLOR_BUCKETS.items():
        if k in c0: return v
    return c0.title() if c0 else None
