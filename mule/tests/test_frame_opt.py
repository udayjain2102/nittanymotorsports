"""frame_opt.py: the committed sizing passes every gate, and the source writer only touches the named group."""
import frame_opt as O


def test_current_sizing_passes_all_gates():
    good, worst, tors, kg, _ = O.evaluate({})
    assert good, (worst, tors)


def test_write_changes_only_the_named_group(tmp_path):
    p = tmp_path / "m.py"
    p.write_text('("a", "b", "C", "Front hoop lower brace"), ("c", "d", "C", "Rear side diagonal")\n')
    O.write({("Front hoop lower brace", "C"): "B"}, p)
    assert p.read_text() == '("a", "b", "B", "Front hoop lower brace"), ("c", "d", "C", "Rear side diagonal")\n'
