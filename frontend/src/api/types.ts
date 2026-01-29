export type BuildingOut = {
  id: number
  address: string
  latitude: number
  longitude: number
}

export type ActivityOut = {
  id: number
  name: string
  parent_id: number | null
  level: number
}

export type OrganizationOut = {
  id: number
  name: string
  phones: string[]
  building: BuildingOut
  activities: ActivityOut[]
}

