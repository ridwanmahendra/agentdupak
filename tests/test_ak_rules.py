from agentdupak.models import Aktivitas
from agentdupak.rules.ak_rules import terapkan


def test_kategori_tanpa_rule_tidak_menggagalkan_sync():
    """Kategori yang sama sekali belum pernah diberi rule (beda dari
    'pendidikan.bimbingan_publikasi_ilmiah' yang sekarang sudah ada rule-nya)
    tidak boleh bikin terapkan() melempar exception -- mekanisme fail-soft ini
    yang menyelamatkan sync dari kategori baru yang belum dikonfirmasi AK-nya."""
    aktivitas = [Aktivitas(kategori="kategori.belum.ada.rule", dosen="", sumber_file="x.pdf")]

    hasil, peringatan = terapkan(aktivitas)

    assert hasil[0].ak == 0.0
    assert hasil[0].ak_perlu_review is True
    assert len(peringatan) == 1
    assert "kategori.belum.ada.rule" in peringatan[0]
