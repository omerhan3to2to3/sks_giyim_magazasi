# Giyim Mağazası - RFID Satış Sistemi

İki bilgisayarda çalışan, merkezi veritabanına bağlı kıyafet satış ve bakiye yükleme sistemi.

## Sistem Mimarisi

```
[Bilgisayar 1 - Para Yükleme]     [Bilgisayar 2 - Satış]
         |                                  |
         +-------- HTTP API (FastAPI) -------+
                         |
                   SQLite Veritabanı
```

Her iki bilgisayar da aynı sunucuya bağlanır. Bir bilgisayardan yüklenen bakiye, diğer bilgisayardan anında kullanılabilir.

## Gereksinimler

- Python 3.10+
- Arduino Nano + **UTR-625** RFID okuyucu (Utarit)
- Windows (test edildi)

## Kurulum

### 1. Sunucuyu başlatın (para yükleme bilgisayarında)

```bat
start_server.bat
```

Sunucu `http://0.0.0.0:8000` adresinde çalışır.

### 2. IP adresini öğrenin

Para yükleme bilgisayarında CMD'de:

```bat
ipconfig
```

IPv4 adresini not alın (örn: `192.168.1.10`).

### 3. Her iki bilgisayarda istemciyi başlatın

```bat
start_client.bat
```

Ana sayfadaki **Bağlantı Ayarları** bölümünden:
- **Sunucu Adresi:** `http://192.168.1.10:8000` (sunucu bilgisayarın IP'si)
- **RFID Port:** Arduino'nun bağlı olduğu COM portu (örn: `COM3`)

## Arduino Kurulumu (UTR-625)

1. `utarit_rfid/utarit_rfid.ino` dosyasını Arduino IDE ile açın
2. Arduino Nano'ya yükleyin (ek kütüphane gerekmez, SoftwareSerial dahili)
3. Bağlantılar:

| UTR-625 | Arduino Nano |
|---------|--------------|
| TX | D10 |
| RX | D11 |
| GND | GND |
| VCC | 5V |

4. USB ile bilgisayara bağlayın, COM portunu istemci ayarlarından seçin

Serial Monitor (9600 baud) açıldığında `RFID:HAZIR` görünmeli; kart okutunca `UID:ABCD1234` gelir.

## Kullanım

### Para Yükleme
1. **Para Yükleme** sayfasına gidin
2. Tutarı girin (50/100/200/500 TL kısayolları veya manuel)
3. Kartı RFID okuyucuya okutun
4. Kart kayıtlı değilse kayıt formu açılır (ad, soyad, e-posta, telefon)
5. Kayıt sonrası bakiye 0 TL olur; para yükleme işlemi tamamlanır

### Alışveriş
1. **Alışveriş** sayfasına gidin
2. Sağ üstten **Ürün Ekle** ile fotoğraf, ürün ID, ad, fiyat ve stok ekleyin
3. Ürünleri sepete ekleyin
4. **Alışverişi Tamamla** → kartı okutun → bakiye düşülür

### İstatistikler
- Ürün stok ve satış istatistikleri
- Müşteri bazlı alışveriş detayları (kim ne aldı)
- **Excel İndir** ile tüm raporları dışa aktarma

## Test Modu (RFID olmadan)

Para Yükleme sayfasının altındaki **Simüle Et** alanına test kart UID'si yazarak deneme yapabilirsiniz.

## Proje Yapısı

```
giyim_magazasi/
├── server/          # FastAPI + SQLite API
├── client/          # CustomTkinter masaüstü uygulaması
├── utarit_rfid/     # UTR-625 RFID okuyucu kodu (ana)
├── arduino/         # Eski MFRC522 kodu (yedek)
├── start_server.bat
└── start_client.bat
```

## Sorun Giderme

| Sorun | Çözüm |
|-------|-------|
| Sunucuya bağlanılamıyor | Windows Güvenlik Duvarı'nda 8000 portunu açın |
| RFID port bulunamadı | Aygıt Yöneticisi'nden COM portunu kontrol edin |
| Kart okunmuyor | `utarit_rfid.ino` yüklü mü? TX→D10, RX→D11 bağlantısını kontrol edin |
