import type { UserSearchResult } from "../types/user/userSearchResult";

export const mockUsers: UserSearchResult[] = [
  {
    id: "4bf4215f-aea7-4114-8a53-52a5e34a3f8f",
    username: "alexpop",
    email: "alex.popescu@gmail.com",
    avatarUrl: "https://randomuser.me/api/portraits/men/1.jpg",
    isFriend: false,
    hasPendingRequest: false,
  },
  {
    id: "7b44c31a-c9e6-425d-9af1-f364205368fa",
    username: "mariai",
    email: "maria.ionescu@yahoo.com",
    avatarUrl: "https://randomuser.me/api/portraits/women/2.jpg",
    isFriend: false,
    hasPendingRequest: false,
  },
  {
    id: "3874118e-83fb-4d65-83b2-dee80003e6a2",
    username: "danstan",
    email: "daniel.stan@github.com",
    avatarUrl: "https://randomuser.me/api/portraits/men/3.jpg",
    isFriend: false,
    hasPendingRequest: false,
  },
  {
    id: "eba8f8cb-15ab-4d41-997b-9b5751b7c896",
    username: "andreeav",
    email: "andreea.vasilescu@gmail.com",
    avatarUrl: "https://randomuser.me/api/portraits/women/4.jpg",
    isFriend: false,
    hasPendingRequest: false,
  },
  {
    id: "c1f3e8d2-5f4b-4e2a-9f3a-2b6e5d9f7c3b",
    username: "DONTEXIST",
    email: "dont@gmail.com",
    avatarUrl: null,
    isFriend: false,
    hasPendingRequest: false,
  }
];
