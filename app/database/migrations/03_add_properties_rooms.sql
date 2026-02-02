-- 1. Create Properties Table
CREATE TABLE IF NOT EXISTS properties (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    owner_id UUID REFERENCES owners(id) ON DELETE CASCADE,
    name VARCHAR(100) NOT NULL DEFAULT 'Main Building',
    address TEXT,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- 2. Create Rooms Table
CREATE TABLE IF NOT EXISTS rooms (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    property_id UUID REFERENCES properties(id) ON DELETE CASCADE,
    room_number VARCHAR(20) NOT NULL,
    floor_number INTEGER DEFAULT 0,
    capacity INTEGER DEFAULT 2, -- Default beds per room
    rent_amount INTEGER DEFAULT 0,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    
    -- Ensure room number is unique per property
    CONSTRAINT uq_room_property UNIQUE (property_id, room_number)
);

-- 3. Update Tenants Table to link to Rooms
ALTER TABLE tenants ADD COLUMN IF NOT EXISTS room_id UUID REFERENCES rooms(id) ON DELETE SET NULL;
