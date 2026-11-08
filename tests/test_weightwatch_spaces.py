"""Tiny numerical checks of vector spaces, independent of model/artifact loading.

WeightWatch v1 section3 explicitly places U in the output space:
https://arxiv.org/html/2508.00161v1#S3
These tests validate our geometry, not a reproduction of its detector.
"""
import pytest
import torch

from model_customs.forensics import (
    activation_direction_alignment,
    cosine_alignment,
    factor_svd,
)


def test_non_square_delta_pairs_input_with_right_and_output_with_left():
    # W has two outputs and three inputs. Its one nonzero input direction is e1.
    a = torch.tensor([[0.0, 1.0, 0.0]])
    b = torch.tensor([[3.0], [4.0]])
    delta = 2.0 * b @ a
    u, singular_values, vh = factor_svd(a, b, scaling=2.0)
    assert torch.allclose(delta, u @ torch.diag(singular_values) @ vh, atol=1e-6)
    inputs = torch.stack([vh[0], -vh[0], torch.tensor([1.0, 0.0, 0.0])])
    outputs = inputs @ delta.T
    expected_magnitude = torch.tensor([[1.0], [1.0], [0.0]])

    right_alignment = activation_direction_alignment(
        inputs.unsqueeze(0), vh, activation_space='input', vector_side='right'
    )
    left_alignment = activation_direction_alignment(
        outputs.unsqueeze(0), u.T, activation_space='output', vector_side='left'
    )
    # Compare magnitudes in paired spaces, not arbitrary SVD vector signs.
    assert right_alignment.shape == left_alignment.shape == (3, 1)
    assert torch.allclose(right_alignment, expected_magnitude, atol=1e-6)
    assert torch.allclose(left_alignment, expected_magnitude, atol=1e-6)


@pytest.mark.parametrize('activation_space,vector_side', [('input', 'left'), ('output', 'right')])
def test_wrong_vector_side_rejected_even_when_square_width_could_hide_it(activation_space, vector_side):
    with pytest.raises(ValueError):
        activation_direction_alignment(
            torch.eye(2), torch.eye(2), activation_space=activation_space, vector_side=vector_side
        )


@pytest.mark.parametrize('directions', [torch.ones(1, 2), torch.ones(3, 1)])
def test_direction_width_must_match_activation_space(directions):
    # Directions are rows. A column vector with the right number of entries is
    # still the wrong orientation; silently transposing could confuse U and Vh.
    with pytest.raises(ValueError):
        activation_direction_alignment(
            torch.ones(2, 3), directions, activation_space='input', vector_side='right'
        )


def test_absolute_alignment_and_delta_are_invariant_to_svd_sign_choice():
    activations = torch.tensor([[3.0, 4.0, 0.0], [-3.0, -4.0, 0.0], [0.0, 0.0, 2.0]])
    directions = torch.tensor([[1.0, 0.0, 0.0], [0.0, 1.0, 0.0]])
    expected = torch.tensor([[0.6, 0.8], [0.6, 0.8], [0.0, 0.0]])
    assert torch.allclose(cosine_alignment(activations, directions), expected)
    assert torch.allclose(cosine_alignment(activations, -directions), expected)
    assert torch.allclose(cosine_alignment(-activations, directions), expected)

    a = torch.tensor([[0.0, 1.0, 0.0]])
    b = torch.tensor([[3.0], [4.0]])
    u, singular_values, vh = factor_svd(a, b, scaling=2.0)
    original = u @ torch.diag(singular_values) @ vh
    reflected = (-u) @ torch.diag(singular_values) @ (-vh)
    assert torch.allclose(original, reflected)
    assert torch.allclose(original, 2.0 * b @ a, atol=1e-6)
