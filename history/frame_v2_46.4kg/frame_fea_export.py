"""Frame-only STEP for Fusion Simulation (NM26_Frame_FEA.step), Z-up, one body per tube.

In Fusion: Modify > Combine (Join) all bodies -> one welded body, then Simulation.
(OCCT segfaults unioning these hollow tubes; Fusion's kernel handles it.)
"""
import cadquery as cq
import mule as m

frame = cq.Compound.makeCompound([m.tube(a, b, s) for a, b, s, _ in m.MEMBERS])
zup = frame.rotate(cq.Vector(), cq.Vector(1, 0, 0), 90)
import pathlib
cq.exporters.export(cq.Workplane().add(zup), str(pathlib.Path(__file__).parent / "cad" / "simple" / "NM26_Frame_FEA.step"))
print(f"{len(zup.Solids())} tube bodies")
