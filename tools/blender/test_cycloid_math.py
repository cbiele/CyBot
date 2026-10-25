import math
import pytest
import cycloid_math as C


def test_outline_has_no_undercut():
    assert C.self_intersections(C.profile(n=720, clear=0.0)) == 0


def test_outline_root_and_tip():
    rs = [math.hypot(x, y) for x, y in C.profile()]
    assert min(rs) == pytest.approx(C.R - C.RP - C.CLEAR - C.E, abs=0.02)
    assert max(rs) == pytest.approx(C.R - C.RP - C.CLEAR + C.E, abs=0.02)


@pytest.mark.parametrize("disk", ["A", "B"])
@pytest.mark.parametrize("theta", [0.0, 0.7, 2.1, 3.9, 5.5])
def test_disk_meshes_with_every_pin(disk, theta):
    gaps = C.pin_gaps(C.disk_outline(disk, theta, n=2880))
    assert min(gaps) >= C.CLEAR - 0.03
    assert max(gaps) <= C.CLEAR + 0.03


def test_disk_a_on_the_front_eccentric_cuts_into_the_pins():
    a = C.disk_outline("A", 0.0)
    on_b_eccentric = [(x - 2 * C.E, y) for x, y in a]
    assert min(C.pin_gaps(on_b_eccentric)) < -0.5


@pytest.mark.parametrize("theta", [0.0, 1.3, 4.4])
def test_output_pins_roll_round_the_bushing_bores(theta):
    for disk in ("A", "B"):
        for hole, pin in zip(C.bushing_centres(disk, theta), C.output_pins(theta)):
            assert math.dist(hole, pin) == pytest.approx(C.E, abs=1e-9)


def test_spring_pins_sized_uncompressed():
    assert 2 * C.OUT_PIN_R >= 4.3
    assert 2 * C.RP >= 3.2


def test_output_pins_run_free_in_the_bushings():
    assert C.BUSHING_BORE_R == 3.0
    assert C.BUSHING_BORE_R - C.OUT_PIN_R - C.E == pytest.approx(C.PIN_RUN_CLEAR / 2)
    assert C.PIN_RUN_CLEAR >= 0.1


def test_disk_clears_the_housing_bore():
    for theta in (0.0, 0.4, 2.0):
        assert max(math.hypot(x, y) for x, y in C.disk_outline("A", theta)) < C.DISK_ZONE_BORE_R - 0.3


def test_belt_centre_distance_for_the_232_belt():
    assert C.belt_centre_distance(20, 40, 232) == pytest.approx(85.76, abs=0.05)


def test_motor_slot_covers_belt_tolerance():
    c = C.belt_centre_distance(20, 40, 232)
    for length in (226, 238):
        assert abs(C.belt_centre_distance(20, 40, length) - c) <= C.MOTOR_SLOT


def test_steps_per_output_degree():
    assert C.STEPS_PER_DEG == pytest.approx(355.56, abs=0.01)
