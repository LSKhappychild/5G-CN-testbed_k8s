/**
 * SPDX-License-Identifier: Apache-2.0
 * © Copyright 2019 The Free5GC Authors
 * © Copyright 2025 Free Mobile SAS
 */
package sidf

import (
	"crypto/ecdh"
	"encoding/hex"
	"errors"
	"fmt"
	"math/rand/v2"
	"testing"
)

var testHomeNetworkPrivateKeys = []HomeNetworkPrivateKey{
	{
		ProtectionScheme: "1", // Protect Scheme: Profile A
		PrivateKey:       Must(ecdh.X25519().NewPrivateKey(Must(hex.DecodeString("c53c22208b61860b06c62e5406a7b330c2b577aa5558981510d128247d38bd1d")))),
		PublicKey:        Must(ecdh.X25519().NewPublicKey(Must(hex.DecodeString("5a8d38864820197c3394b92613b20b91633cbd897119273bf8e4a6f4eec0a650")))),
	},
	{
		ProtectionScheme: "2", // Protect Scheme: Profile B
		PrivateKey:       Must(ecdh.P256().NewPrivateKey(Must(hex.DecodeString("F1AB1074477EBCC7F554EA1C5FC368B1616730155E0041AC447D6301975FECDA")))),
		PublicKey:        Must(ecdh.P256().NewPublicKey(Must(hex.DecodeString("0472DA71976234CE833A6907425867B82E074D44EF907DFB4B3E21C1C2256EBCD15A7DED52FCBB097A4ED250E036C7B9C8C7004C4EEDC4F068CD7BF8D3F900E3B4")))),
	},
	{
		ProtectionScheme: "2", // Protect Scheme: Profile B
		PrivateKey:       Must(ecdh.P256().NewPrivateKey(Must(hex.DecodeString("F1AB1074477EBCC7F554EA1C5FC368B1616730155E0041AC447D6301975FECDA")))),
		PublicKey:        Must(ecdh.P256().NewPublicKey(Must(hex.DecodeString("0472DA71976234CE833A6907425867B82E074D44EF907DFB4B3E21C1C2256EBCD15A7DED52FCBB097A4ED250E036C7B9C8C7004C4EEDC4F068CD7BF8D3F900E3B4")))),
	},
}

var testHomeNetworkPublicKeys = []HomeNetworkPublicKey{
	{
		ProtectionScheme: "1",
		PublicKeyID:      "1",
		PublicKey:        Must(ecdh.X25519().NewPublicKey(Must(hex.DecodeString("5a8d38864820197c3394b92613b20b91633cbd897119273bf8e4a6f4eec0a650")))),
	},
	{
		ProtectionScheme: "2",
		PublicKeyID:      "2",
		PublicKey:        Must(ecdh.P256().NewPublicKey(Must(hex.DecodeString("0472DA71976234CE833A6907425867B82E074D44EF907DFB4B3E21C1C2256EBCD15A7DED52FCBB097A4ED250E036C7B9C8C7004C4EEDC4F068CD7BF8D3F900E3B4")))),
	},
	{
		ProtectionScheme: "2",
		PublicKeyID:      "3",
		PublicKey:        Must(ecdh.P256().NewPublicKey(Must(hex.DecodeString("0472DA71976234CE833A6907425867B82E074D44EF907DFB4B3E21C1C2256EBCD15A7DED52FCBB097A4ED250E036C7B9C8C7004C4EEDC4F068CD7BF8D3F900E3B4")))),
	},
}

func TestToSupi(t *testing.T) {
	testCases := []struct {
		suci         string
		expectedSupi string
		expectedErr  error
	}{
		{
			suci:         "suci-0-208-93-0-0-0-00007487",
			expectedSupi: "imsi-2089300007487",
			expectedErr:  nil,
		},
		{
			suci: "suci-0-208-93-0-1-1-b2e92f836055a255837debf850b528997ce0201cb82a" +
				"dfe4be1f587d07d8457dcb02352410cddd9e730ef3fa87",
			expectedSupi: "imsi-20893001002086",
			expectedErr:  nil,
		},
		{
			suci: "suci-0-208-93-0-2-2-039aab8376597021e855679a9778ea0b67396e68c66d" +
				"f32c0f41e9acca2da9b9d146a33fc2716ac7dae96aa30a4d",
			expectedSupi: "imsi-20893001002086",
			expectedErr:  nil,
		},
		{
			suci: "suci-0-208-93-0-2-2-0434a66778799d52fedd9326db4b690d092e05c9ba0ace5b413da" +
				"fc0a40aa28ee00a79f790fa4da6a2ece892423adb130dc1b30e270b7d0088bdd716b93894891d5221a74c810d6b9350cc067c76",
			expectedSupi: "",
			expectedErr:  ErrorPublicKeyUnmarshalling,
		},
		{
			suci: "suci-0-001-01-0-2-2-03a7b1db2a9db9d44112b59d03d8243dc6089fd91d2ecb" +
				"78f5d16298634682e94373888b22bdc9293d1681922e17",
			expectedSupi: "imsi-001010123456789",
			expectedErr:  nil,
		},
		{
			// Uncompressed Ephemeral Public Key + Compressed Home Public Key
			suci: "suci-0-001-01-0-2-2-049AAB8376597021E855679A9778EA0B67396E68C66DF32C0F41E9ACCA2DA9B9D1D1F44EA1C" +
				"87AA7478B954537BDE79951E748A43294A4F4CF86EAFF1789C9C81F46A33FC2716AC7DAE96AA30A4D",
			expectedSupi: "imsi-00101001002086",
			expectedErr:  nil,
		},
		{
			suci: "suci-0-208-93-0-2-3-039aab8376597021e855679a9778ea0b67396e68c66d" +
				"f32c0f41e9acca2da9b9d146a33fc2716ac7dae96aa30a4d",
			expectedSupi: "imsi-20893001002086",
			expectedErr:  nil,
		},
		{
			suci: "suci-0-208-93-0-2-3-0434a66778799d52fedd9326db4b690d092e05c9ba0ace5b413da" +
				"fc0a40aa28ee00a79f790fa4da6a2ece892423adb130dc1b30e270b7d0088bdd716b93894891d5221a74c810d6b9350cc067c76",
			expectedSupi: "",
			expectedErr:  ErrorPublicKeyUnmarshalling,
		},
		{
			suci: "suci-0-001-01-0-2-3-03a7b1db2a9db9d44112b59d03d8243dc6089fd91d2ecb" +
				"78f5d16298634682e94373888b22bdc9293d1681922e17",
			expectedSupi: "imsi-001010123456789",
			expectedErr:  nil,
		},
		{
			// Uncompressed Ephemeral Public Key + Uncompressed Home Public Key
			suci: "suci-0-001-01-0-2-3-049AAB8376597021E855679A9778EA0B67396E68C66DF32C0F41E9ACCA2DA9B9D1D1F44EA1C" +
				"87AA7478B954537BDE79951E748A43294A4F4CF86EAFF1789C9C81F46A33FC2716AC7DAE96AA30A4D",
			expectedSupi: "imsi-00101001002086",
			expectedErr:  nil,
		},
	}
	for i, tc := range testCases {
		supi, err := ToSupi(tc.suci, testHomeNetworkPrivateKeys)
		if err != nil {
			if !errors.Is(err, tc.expectedErr) {
				t.Errorf("TC%d fail: err[%v], expected[%v]\n", i, err, tc.expectedErr)
			}
		} else if supi != tc.expectedSupi {
			t.Errorf("TC%d fail: supi[%s], expected[%s]\n", i, supi, tc.expectedSupi)
		}
	}
}

func TestSupiToSuciToSupi(t *testing.T) {
	testCases := []string{"0010020862"}

	for _ = range 100 {
		testCases = append(testCases, fmt.Sprintf("%010d", rand.Int64N(10000000000)))
	}

	for i, tc := range testCases {
		suci, err := CipherSuci(tc, "208", "15", "0", testHomeNetworkPublicKeys[2])
		if err != nil {
			t.Errorf("TC%d fail: %v", i, tc)
		}
		decipheredSupi, err := ToSupi(suci.Raw, testHomeNetworkPrivateKeys)
		if err != nil {
			t.Errorf("TC%d fail: unable to deciphber ciphered suci: %v", i, err)
		}
		if decipheredSupi != "imsi-20815"+tc {
			t.Errorf("TC%d fail: decipheredSupi[%s] != supi[20815%s]", i, decipheredSupi, tc)
		}
	}
}

func Must[T any](v T, err error) T {
	if err != nil {
		panic(err)
	}
	return v
}
