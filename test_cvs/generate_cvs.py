"""
Generate 4 sample CV PDFs in Turkish for testing a CV screening system.
Uses reportlab with DejaVuSans font for proper Turkish character support.
"""

import os
import sys
from reportlab.lib.pagesizes import A4
from reportlab.lib.units import cm, mm
from reportlab.lib.colors import HexColor, black, white
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.enums import TA_LEFT, TA_CENTER, TA_JUSTIFY
from reportlab.platypus import (
    SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle,
    HRFlowable
)
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont

# ---------------------------------------------------------------------------
# Font registration - find and register a font that supports Turkish chars
# ---------------------------------------------------------------------------
def register_turkish_font():
    """Register a font that supports Turkish characters (ğ, ü, ş, ı, ö, ç, İ)."""
    # Try common font paths on Windows
    font_candidates = [
        ("DejaVuSans", "C:/Windows/Fonts/DejaVuSans.ttf"),
        ("DejaVuSans", "C:/Windows/Fonts/dejavu-sans/DejaVuSans.ttf"),
        ("Arial", "C:/Windows/Fonts/arial.ttf"),
        ("Calibri", "C:/Windows/Fonts/calibri.ttf"),
        ("Segoe UI", "C:/Windows/Fonts/segoeui.ttf"),
        ("Tahoma", "C:/Windows/Fonts/tahoma.ttf"),
        ("Verdana", "C:/Windows/Fonts/verdana.ttf"),
    ]

    bold_candidates = [
        ("DejaVuSans-Bold", "C:/Windows/Fonts/DejaVuSans-Bold.ttf"),
        ("DejaVuSans-Bold", "C:/Windows/Fonts/dejavu-sans/DejaVuSans-Bold.ttf"),
        ("Arial-Bold", "C:/Windows/Fonts/arialbd.ttf"),
        ("Calibri-Bold", "C:/Windows/Fonts/calibrib.ttf"),
        ("Segoe UI Bold", "C:/Windows/Fonts/segoeuib.ttf"),
        ("Tahoma-Bold", "C:/Windows/Fonts/tahomabd.ttf"),
        ("Verdana-Bold", "C:/Windows/Fonts/verdanab.ttf"),
    ]

    regular_name = None
    bold_name = None

    for name, path in font_candidates:
        if os.path.exists(path):
            font_name = "TurkishRegular"
            try:
                pdfmetrics.registerFont(TTFont(font_name, path))
                regular_name = font_name
                print(f"  Registered regular font: {name} from {path}")
                break
            except Exception as e:
                print(f"  Failed to register {name}: {e}")
                continue

    for name, path in bold_candidates:
        if os.path.exists(path):
            font_name = "TurkishBold"
            try:
                pdfmetrics.registerFont(TTFont(font_name, path))
                bold_name = font_name
                print(f"  Registered bold font: {name} from {path}")
                break
            except Exception as e:
                print(f"  Failed to register {name}: {e}")
                continue

    if regular_name is None:
        print("WARNING: Could not find a suitable Turkish font. Falling back to Helvetica.")
        regular_name = "Helvetica"
        bold_name = "Helvetica-Bold"

    if bold_name is None:
        bold_name = regular_name

    return regular_name, bold_name


# ---------------------------------------------------------------------------
# Style helpers
# ---------------------------------------------------------------------------
DARK_BLUE = HexColor("#1a3c5e")
MEDIUM_BLUE = HexColor("#2c5f8a")
LIGHT_BLUE = HexColor("#e8f0f8")
DARK_GRAY = HexColor("#333333")
MEDIUM_GRAY = HexColor("#666666")
LIGHT_GRAY = HexColor("#f5f5f5")
ACCENT = HexColor("#2c5f8a")


def create_styles(regular_font, bold_font):
    """Create paragraph styles for CV layout."""
    styles = {}

    styles["Name"] = ParagraphStyle(
        "Name",
        fontName=bold_font,
        fontSize=20,
        leading=24,
        textColor=DARK_BLUE,
        spaceAfter=2 * mm,
    )

    styles["Contact"] = ParagraphStyle(
        "Contact",
        fontName=regular_font,
        fontSize=9,
        leading=13,
        textColor=MEDIUM_GRAY,
        spaceAfter=4 * mm,
    )

    styles["SectionTitle"] = ParagraphStyle(
        "SectionTitle",
        fontName=bold_font,
        fontSize=12,
        leading=16,
        textColor=DARK_BLUE,
        spaceBefore=6 * mm,
        spaceAfter=3 * mm,
    )

    styles["SubTitle"] = ParagraphStyle(
        "SubTitle",
        fontName=bold_font,
        fontSize=10,
        leading=14,
        textColor=DARK_GRAY,
        spaceAfter=1 * mm,
    )

    styles["DateRange"] = ParagraphStyle(
        "DateRange",
        fontName=regular_font,
        fontSize=9,
        leading=12,
        textColor=MEDIUM_GRAY,
        spaceAfter=1 * mm,
    )

    styles["Body"] = ParagraphStyle(
        "Body",
        fontName=regular_font,
        fontSize=9.5,
        leading=13,
        textColor=DARK_GRAY,
        spaceAfter=2 * mm,
        alignment=TA_JUSTIFY,
    )

    styles["Bullet"] = ParagraphStyle(
        "Bullet",
        fontName=regular_font,
        fontSize=9.5,
        leading=13,
        textColor=DARK_GRAY,
        leftIndent=10,
        spaceAfter=1 * mm,
        bulletIndent=0,
    )

    styles["SkillLabel"] = ParagraphStyle(
        "SkillLabel",
        fontName=bold_font,
        fontSize=9.5,
        leading=13,
        textColor=DARK_GRAY,
    )

    styles["SkillValue"] = ParagraphStyle(
        "SkillValue",
        fontName=regular_font,
        fontSize=9.5,
        leading=13,
        textColor=DARK_GRAY,
    )

    return styles


# ---------------------------------------------------------------------------
# CV builder
# ---------------------------------------------------------------------------
def build_cv(filepath, data, regular_font, bold_font):
    """Build a single CV PDF from structured data."""
    styles = create_styles(regular_font, bold_font)

    doc = SimpleDocTemplate(
        filepath,
        pagesize=A4,
        leftMargin=2 * cm,
        rightMargin=2 * cm,
        topMargin=1.5 * cm,
        bottomMargin=1.5 * cm,
    )

    story = []

    # --- Header: Name ---
    story.append(Paragraph(data["name"], styles["Name"]))

    # --- Contact info ---
    contact_parts = []
    if data.get("phone"):
        contact_parts.append(data["phone"])
    if data.get("email"):
        contact_parts.append(data["email"])
    if data.get("location"):
        contact_parts.append(data["location"])
    if data.get("birth_year"):
        contact_parts.append(f"Dogum: {data['birth_year']}")

    contact_line = "  |  ".join(contact_parts)
    story.append(Paragraph(contact_line, styles["Contact"]))

    # Separator
    story.append(HRFlowable(
        width="100%", thickness=1, color=MEDIUM_BLUE,
        spaceAfter=3 * mm, spaceBefore=1 * mm
    ))

    # --- Ozet ---
    if data.get("summary"):
        story.append(Paragraph("OZET", styles["SectionTitle"]))
        story.append(Paragraph(data["summary"], styles["Body"]))

    # --- Egitim ---
    if data.get("education"):
        story.append(Paragraph("EGITIM", styles["SectionTitle"]))
        story.append(HRFlowable(
            width="100%", thickness=0.5, color=LIGHT_BLUE,
            spaceAfter=2 * mm
        ))
        for edu in data["education"]:
            story.append(Paragraph(edu["degree"], styles["SubTitle"]))
            story.append(Paragraph(
                f"{edu['school']}  |  {edu['dates']}", styles["DateRange"]
            ))
            if edu.get("details"):
                story.append(Paragraph(edu["details"], styles["Body"]))

    # --- Is Deneyimi ---
    if data.get("experience"):
        story.append(Paragraph("IS DENEYIMI", styles["SectionTitle"]))
        story.append(HRFlowable(
            width="100%", thickness=0.5, color=LIGHT_BLUE,
            spaceAfter=2 * mm
        ))
        for exp in data["experience"]:
            story.append(Paragraph(
                f"{exp['title']}  -  {exp['company']}", styles["SubTitle"]
            ))
            story.append(Paragraph(exp["dates"], styles["DateRange"]))
            if exp.get("bullets"):
                for bullet in exp["bullets"]:
                    story.append(Paragraph(
                        f"\u2022  {bullet}", styles["Bullet"]
                    ))
            story.append(Spacer(1, 2 * mm))

    # --- Teknik Beceriler ---
    if data.get("skills"):
        story.append(Paragraph("TEKNIK BECERILER", styles["SectionTitle"]))
        story.append(HRFlowable(
            width="100%", thickness=0.5, color=LIGHT_BLUE,
            spaceAfter=2 * mm
        ))
        for category, items in data["skills"].items():
            skill_text = f"<b>{category}:</b>  {items}"
            story.append(Paragraph(skill_text, styles["Body"]))

    # --- Yabanci Diller ---
    if data.get("languages"):
        story.append(Paragraph("YABANCI DILLER", styles["SectionTitle"]))
        story.append(HRFlowable(
            width="100%", thickness=0.5, color=LIGHT_BLUE,
            spaceAfter=2 * mm
        ))
        lang_parts = []
        for lang, level in data["languages"].items():
            lang_parts.append(f"{lang}: {level}")
        story.append(Paragraph("  |  ".join(lang_parts), styles["Body"]))

    # --- Sertifikalar ---
    if data.get("certificates"):
        story.append(Paragraph("SERTIFIKALAR", styles["SectionTitle"]))
        story.append(HRFlowable(
            width="100%", thickness=0.5, color=LIGHT_BLUE,
            spaceAfter=2 * mm
        ))
        for cert in data["certificates"]:
            story.append(Paragraph(f"\u2022  {cert}", styles["Bullet"]))

    # --- Referanslar ---
    story.append(Paragraph("REFERANSLAR", styles["SectionTitle"]))
    story.append(HRFlowable(
        width="100%", thickness=0.5, color=LIGHT_BLUE,
        spaceAfter=2 * mm
    ))
    story.append(Paragraph("Istek uzerine sunulabilir.", styles["Body"]))

    # Build
    doc.build(story)
    print(f"  [OK] {os.path.basename(filepath)} olusturuldu.")


# ---------------------------------------------------------------------------
# CV data definitions
# ---------------------------------------------------------------------------

def get_cv_data():
    """Return a list of CV data dictionaries."""

    cv1 = {
        "name": "Ahmet Yilmaz",
        "phone": "+90 532 111 22 33",
        "email": "ahmet.yilmaz@email.com",
        "location": "Istanbul, Turkiye",
        "birth_year": "1998",
        "summary": (
            "5 yillik yazilim gelistirme deneyimine sahip, full-stack web teknolojileri "
            "ve ERP entegrasyonlari konusunda uzman yazilim muhendisi. Uretim sektorunde "
            "dijital donusum projelerinde aktif rol almis, agile metodolojilere hakim, "
            "takim liderligine yatkun bir profesyonel."
        ),
        "education": [
            {
                "degree": "Bilgisayar Muhendisligi Lisans",
                "school": "Istanbul Teknik Universitesi (ITU)",
                "dates": "2016 - 2020",
                "details": "Genel Not Ortalamasi: 3.45/4.00. Bitirme projesi: Bulut tabanli ERP modulu gelistirme.",
            }
        ],
        "experience": [
            {
                "title": "Kidemli Yazilim Gelistirici",
                "company": "TechPro Yazilim A.S.",
                "dates": "Ocak 2023 - Halen",
                "bullets": [
                    "React ve Node.js ile musteri yonetim sistemi gelistirilmesi; 15+ modulu kapsayan mikro-servis mimarisi tasarimi.",
                    "PostgreSQL veritabani optimizasyonu ile sorgu surelerinde %40 iyilestirme saglandi.",
                    "Docker ve Kubernetes ile CI/CD pipeline kurulumu ve yonetimi.",
                    "3 kisilik gelistirici ekibine teknik mentorluk ve code review surecleri yonetimi.",
                ],
            },
            {
                "title": "Yazilim Gelistirici",
                "company": "CamTech Endustri (Yorglass tedarikci firmasi)",
                "dates": "Haziran 2020 - Aralik 2022",
                "bullets": [
                    "Uretim hatti icin SAP ERP entegrasyonu: Python tabanli middleware gelistirme.",
                    "Cam uretim sureclerinde kalite kontrol dashboard'u olusturma (React + D3.js).",
                    "REST API tasarimi ve dokumantasyonu; 50+ endpoint gelistirilmesi.",
                    "Uretim verimliligi raporlama sistemi ile %25 maliyet tasarrufu saglandi.",
                ],
            },
        ],
        "skills": {
            "Programlama Dilleri": "Python, JavaScript/TypeScript, Java, SQL",
            "Frontend": "React, Next.js, HTML5, CSS3, Tailwind CSS",
            "Backend": "Node.js, Express, FastAPI, Django",
            "Veritabani": "PostgreSQL, MongoDB, Redis",
            "DevOps": "Docker, Kubernetes, GitHub Actions, AWS (EC2, S3, Lambda)",
            "Diger": "Git, Jira, Agile/Scrum, RESTful API, GraphQL",
        },
        "languages": {
            "Ingilizce": "C1 (Ileri duzey)",
            "Almanca": "A2 (Temel duzey)",
        },
        "certificates": [
            "AWS Certified Developer - Associate (2023)",
            "Scrum Master Sertifikasi - PSM I (2022)",
            "Python Professional Certificate - PCPP (2021)",
        ],
    }

    cv2 = {
        "name": "Elif Demir",
        "phone": "+90 544 222 33 44",
        "email": "elif.demir@email.com",
        "location": "Sakarya, Turkiye",
        "birth_year": "2002",
        "summary": (
            "Yazilim muhendisligi mezunu, 2 yillik deneyime sahip junior yazilim gelistirici. "
            "Web gelistirme ve veritabani yonetimi konularinda temel bilgilere sahip, "
            "ogrenmeye acik ve takim calismasina yatkun bir profesyonel."
        ),
        "education": [
            {
                "degree": "Yazilim Muhendisligi Lisans",
                "school": "Sakarya Universitesi",
                "dates": "2018 - 2022",
                "details": "Genel Not Ortalamasi: 2.85/4.00.",
            }
        ],
        "experience": [
            {
                "title": "Junior Yazilim Gelistirici",
                "company": "WebSoft Bilisim Ltd.",
                "dates": "Eylul 2023 - Halen",
                "bullets": [
                    "Kurumsal web sitesi bakimi ve kucuk olcekli yeni ozellik gelistirme.",
                    "Bug fix ve test surecleri; haftalik sprint toplantilarina katilim.",
                    "Python ile basit veri isleme scriptleri yazimi.",
                ],
            },
            {
                "title": "Yazilim Stajyeri",
                "company": "Dijital Cozumler A.S.",
                "dates": "Haziran 2022 - Agustos 2022",
                "bullets": [
                    "HTML, CSS ve JavaScript ile firma ici portal sayfalarinin guncellenmesi.",
                    "SQL sorgulari ile raporlama islemlerine destek.",
                    "Yazilim gelistirme sureclerini ve versiyon kontrolunu (Git) ogrendi.",
                ],
            },
            {
                "title": "Stajyer (Uzun donem)",
                "company": "TeknoLab Bilisim",
                "dates": "Subat 2022 - Mayis 2022",
                "bullets": [
                    "E-ticaret sitesinde urun katalog modulune destek.",
                    "Test senaryolari hazirlama ve manuel test surecleri.",
                ],
            },
        ],
        "skills": {
            "Programlama Dilleri": "Python (Orta), JavaScript (Temel), SQL (Orta)",
            "Frontend": "HTML5, CSS3, Bootstrap",
            "Backend": "Flask (Temel), Node.js (Temel)",
            "Veritabani": "MySQL, SQLite",
            "Diger": "Git, VS Code, Temel Linux komutlari",
        },
        "languages": {
            "Ingilizce": "B1 (Orta duzey)",
        },
        "certificates": [
            "Udemy Python Bootcamp Sertifikasi (2023)",
            "BTK Akademi Web Gelistirme Egitimi (2022)",
        ],
    }

    cv3 = {
        "name": "Mehmet Kaya",
        "phone": "+90 555 333 44 55",
        "email": "mehmet.kaya@email.com",
        "location": "Ankara, Turkiye",
        "birth_year": "1991",
        "summary": (
            "10 yillik pazarlama ve satis deneyimine sahip, isletme mezunu profesyonel. "
            "Marka yonetimi, dijital pazarlama ve musteri iliskileri konularinda genis "
            "tecrube. Satis ekiplerinin yonetimi ve hedef odakli calisma konularinda basarili."
        ),
        "education": [
            {
                "degree": "Isletme Lisans",
                "school": "Anadolu Universitesi",
                "dates": "2009 - 2013",
                "details": "Genel Not Ortalamasi: 2.70/4.00. Pazarlama bolumu.",
            }
        ],
        "experience": [
            {
                "title": "Pazarlama Muduru",
                "company": "GurSatis Ticaret A.S.",
                "dates": "Mart 2020 - Halen",
                "bullets": [
                    "12 kisilik pazarlama ekibinin yonetimi ve stratejik planlama.",
                    "Yillik pazarlama butcesinin (2M TL) planlanmasi ve yonetimi.",
                    "Dijital pazarlama kampanyalariyla marka bilinirliginde %30 artis.",
                    "SAP SD modulu uzerinden satis raporlari takibi (kullanici seviyesi).",
                ],
            },
            {
                "title": "Satis Uzmani",
                "company": "AnadoluPazar Ltd. Sti.",
                "dates": "Ocak 2016 - Subat 2020",
                "bullets": [
                    "B2B satis surecleri yonetimi ve musteri portfoyunun gelistirilmesi.",
                    "Aylik satis raporlarinin Excel ile hazirlanmasi ve yonetime sunulmasi.",
                    "Fuarlara katilim ve urun tanitim sunumlarinin hazirlanmasi (PowerPoint).",
                ],
            },
            {
                "title": "Satis Temsilcisi",
                "company": "MegaMarket Zinciri",
                "dates": "Temmuz 2013 - Aralik 2015",
                "bullets": [
                    "Saha satisi ve musteri ziyaretleri.",
                    "Haftalik satis raporlarinin hazirlanmasi.",
                    "Musteri memnuniyeti anketlerinin yurutulmesi.",
                ],
            },
        ],
        "skills": {
            "Ofis Yazilimlari": "Microsoft Excel (Ileri), PowerPoint (Ileri), Word (Ileri)",
            "Pazarlama Araclari": "Google Analytics, Meta Business Suite, Canva",
            "ERP": "SAP SD Modulu (Kullanici seviyesi)",
            "Diger": "Proje yonetimi, Sunum teknikleri, Musteri iliskileri yonetimi (CRM)",
        },
        "languages": {
            "Ingilizce": "A2 (Baslangic duzey)",
        },
        "certificates": [
            "Google Digital Marketing Sertifikasi (2021)",
            "Satis Yonetimi Egitimi - TOBB (2019)",
        ],
    }

    cv4 = {
        "name": "Zeynep Ozturk",
        "phone": "+90 533 444 55 66",
        "email": "zeynep.ozturk@email.com",
        "location": "Ankara, Turkiye",
        "birth_year": "1999",
        "summary": (
            "Endustri muhendisligi yuksek lisans mezunu, veri analizi ve makine ogrenmesi "
            "konularinda 3 yillik deneyime sahip veri analisti. Uretim sektorunde veri "
            "odakli karar alma sureclerine katki saglamis, SAP ve Power BI ile is zekasi "
            "cozumleri gelistirmis bir profesyonel."
        ),
        "education": [
            {
                "degree": "Endustri Muhendisligi Yuksek Lisans",
                "school": "Orta Dogu Teknik Universitesi (ODTU)",
                "dates": "2021 - 2023",
                "details": "Tez konusu: Cam uretim sureclerinde makine ogrenmesi ile kalite tahmin modeli. GNO: 3.65/4.00.",
            },
            {
                "degree": "Endustri Muhendisligi Lisans",
                "school": "Hacettepe Universitesi",
                "dates": "2017 - 2021",
                "details": "Genel Not Ortalamasi: 3.30/4.00.",
            },
        ],
        "experience": [
            {
                "title": "Veri Analisti",
                "company": "DataVizyon Danismanlik A.S.",
                "dates": "Ekim 2023 - Halen",
                "bullets": [
                    "Uretim sirketleri icin Power BI dashboard gelistirme ve veri modelleme.",
                    "Python ile ETL surecleri olusturma; pandas, numpy kutuphaneleri ile veri temizleme.",
                    "Makine ogrenmesi modelleri (scikit-learn) ile talep tahmin sistemleri gelistirme.",
                    "SAP veri cikislari uzerinden raporlama ve analiz otomasyonu.",
                ],
            },
            {
                "title": "Veri Analizi Stajyeri",
                "company": "Trakya Cam Sanayii A.S.",
                "dates": "Haziran 2022 - Eylul 2022",
                "bullets": [
                    "Cam uretim hattinda kalite kontrol verilerinin analizi.",
                    "Uretim kayip analizleri ile %15 fire oraninda azalma onerileri sunuldu.",
                    "SAP PP modulu uzerinden uretim verilerine erisim ve raporlama.",
                    "Yuksek lisans tezi icin veri toplama ve on isleme calismalari.",
                ],
            },
            {
                "title": "Is Analisti (Part-time)",
                "company": "SmartData Bilisim",
                "dates": "Ocak 2021 - Mayis 2022",
                "bullets": [
                    "SQL ile veritabani sorgulama ve raporlama.",
                    "Excel ile veri analizi ve pivot tablo raporlari olusturma.",
                    "Musteri verilerinin segmentasyon analizi.",
                ],
            },
        ],
        "skills": {
            "Programlama": "Python (Ileri - pandas, numpy, scikit-learn, matplotlib), SQL (Ileri)",
            "Is Zekasi": "Power BI (Ileri), Tableau (Orta), Excel (Ileri)",
            "Makine Ogrenmesi": "Regresyon, Siniflandirma, Kumeleme, Zaman Serisi Analizi",
            "ERP": "SAP PP ve MM Modulleri (Orta duzey kullanici)",
            "Diger": "Git, Jupyter Notebook, Istatistiksel Analiz, Veri Gorsellestirme",
        },
        "languages": {
            "Ingilizce": "B2 (Ortanin ustu)",
        },
        "certificates": [
            "Microsoft Power BI Data Analyst Associate (PL-300) - 2024",
            "Google Data Analytics Professional Certificate (2023)",
            "SAP Temel Kullanici Egitimi Sertifikasi (2022)",
        ],
    }

    return [
        ("cv_ahmet_yilmaz.pdf", cv1),
        ("cv_elif_demir.pdf", cv2),
        ("cv_mehmet_kaya.pdf", cv3),
        ("cv_zeynep_ozturk.pdf", cv4),
    ]


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------
def main():
    output_dir = r"C:\Users\abdul\OneDrive\Desktop\sap_sql_agent\test_cvs"
    os.makedirs(output_dir, exist_ok=True)

    print("Font kaydediliyor...")
    regular_font, bold_font = register_turkish_font()
    print()

    print("CV'ler olusturuluyor...")
    for filename, data in get_cv_data():
        filepath = os.path.join(output_dir, filename)
        build_cv(filepath, data, regular_font, bold_font)

    print()
    print("Tum CV dosyalari basariyla olusturuldu!")
    print(f"Konum: {output_dir}")

    # Verify files
    print()
    print("Dosya dogrulamasi:")
    for filename, _ in get_cv_data():
        filepath = os.path.join(output_dir, filename)
        if os.path.exists(filepath):
            size_kb = os.path.getsize(filepath) / 1024
            print(f"  [OK] {filename} ({size_kb:.1f} KB)")
        else:
            print(f"  [HATA] {filename} bulunamadi!")


if __name__ == "__main__":
    main()
