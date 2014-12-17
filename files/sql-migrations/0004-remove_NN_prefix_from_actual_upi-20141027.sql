

-- UPDATE all party records to remove NN- prefix from the UPI as it is
-- no longer prepended to the UPI but appeneded in the client for display only

UPDATE "party_party" SET ref=substring(ref from 4) where ref ~ 'NN-.+';